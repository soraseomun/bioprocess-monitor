import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MultipleLocator


class BioprocessMonitor:
    def __init__(self, filepath, ph_lims, temperature_lims):
        """
        Utility class used to monitor bioprocesses by
        generating dashboards and summaries.

        Parameters
        ----------
        filepath : str
            Input CSV dataset path.
        ph_lims : tuple[float, float]
            Lower and upper acceptable pH limits.
        temperature_lims : tuple[float, float]
            Lower and upper acceptable temperature limits.
        """
        self.df = pd.read_csv(filepath)
        self.ph_min = ph_lims[0]
        self.ph_max = ph_lims[1]
        self.temp_min = temperature_lims[0]
        self.temp_max = temperature_lims[1]

    def extract_batch(self, batch_id):
        """
        Extracts data corresponding to a single batch.

        Parameters
        ----------
        batch_id : int
            Batch identifier.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing only rows associated with
            the requested batch.
        """
        mask = self.df.loc[:, "batch_id"] == batch_id
        df_batch = self.df.loc[mask, :]
        return df_batch

    def optimal_ph_mask(self, df_batch):
        """
        Determines whether each pH measurement falls within
        the acceptable operating range.

        Parameters
        ----------
        df_batch : pandas.DataFrame
            Batch-specific DataFrame.

        Returns
        -------
        array-like of bool
            A mask whereby True indicates that the measurement
            is within the acceptable operating range.
        """
        ph = df_batch.loc[:, "pH"]
        mask = (ph >= self.ph_min) & (ph <= self.ph_max)
        return mask

    def optimal_temperature_mask(self, df_batch):
        """
        Determines whether each temperature measurement falls
        within the acceptable operating range.

        Parameters
        ----------
        df_batch : pandas.DataFrame
            Batch-specific DataFrame.

        Returns
        -------
        array-like of bool
            A mask whereby True indicates that the measurement
            is within the acceptable operating range.
        """
        temperature = df_batch.loc[:, "temperature_C"]
        mask = (temperature >= self.temp_min) & (temperature <= self.temp_max)
        return mask

    def get_n_batches(self):
        """
        Determines the number of unique batches present
        in the dataset.

        Returns
        -------
        int
            Total number of distinct batch identifiers.
        """
        n_batches = self.df.loc[:, "batch_id"].nunique()
        return n_batches

    def export_dashboard(self, batch_id, filepath):
        """
        Creates and saves a dashboard figure for a single batch.

        Parameters
        ----------
        batch_id : int
            Batch identifier.
        filepath : str
            Output PNG image path.

        Dashboard Requirements
        ----------------------
        Create a 2 × 2 figure containing:

        Top-Left
            Glucose, biomass, and product concentrations versus time.
            - A different color and marker should be used for each substance.

        Top-Right
            Temperature versus time.
            - Measurements within the acceptable temperature range
              should be displayed as green circles.
            - Measurements outside the acceptable temperature range
              should be displayed as red X markers.

        Bottom-Left
            pH versus time.
            - Measurements within the acceptable pH range
              should be displayed as green circles.
            - Measurements outside the acceptable pH range
              should be displayed as red X markers.

        Bottom-Right
            Dissolved oxygen versus time.

        Additional Requirements
        -----------------------
        - Use scatter plots.
        - Add x-axis and y-axis labels.
        - Add legends where appropriate.
        - Apply consistent formatting across all subplots unless
          indicated otherwise.
        - Apply a tick spacing of 6 h on the x-axis for all subplots.
        - Save the figure to the provided filepath.
        - Close the figure after saving.
        """
        df_batch = self.extract_batch(batch_id)
        time = df_batch.loc[:, "time_h"]
        temperature = df_batch.loc[:, "temperature_C"]
        ph = df_batch.loc[:, "pH"]
        temp_ok = self.optimal_temperature_mask(df_batch)
        ph_ok = self.optimal_ph_mask(df_batch)

        # Shared marker style so every subplot looks consistent
        style = dict(s=36, edgecolor="black", linewidth=0.6, alpha=0.75)

        fig, axes = plt.subplots(2, 2, figsize=(12, 8))

        # Top-left: concentrations
        ax = axes[0, 0]
        ax.scatter(time, df_batch.loc[:, "C_glucose_g_L^-1"],
                   color="tab:blue", marker="o", label="Glucose", **style)
        ax.scatter(time, df_batch.loc[:, "C_biomass_g_L^-1"],
                   color="tab:orange", marker="^", label="Biomass", **style)
        ax.scatter(time, df_batch.loc[:, "C_product_g_L^-1"],
                   color="tab:green", marker="s", label="Product", **style)
        ax.set_ylabel("Concentration [g/L]")
        ax.legend()

        # Top-right: temperature
        ax = axes[0, 1]
        ax.scatter(time[temp_ok], temperature[temp_ok],
                   color="tab:green", marker="o", label="Optimal", **style)
        ax.scatter(time[~temp_ok], temperature[~temp_ok],
                   color="tab:red", marker="X", label="Sub-Optimal", **style)
        ax.set_ylabel("Temperature [°C]")
        ax.legend()

        # Bottom-left: pH
        ax = axes[1, 0]
        ax.scatter(time[ph_ok], ph[ph_ok],
                   color="tab:green", marker="o", label="Optimal", **style)
        ax.scatter(time[~ph_ok], ph[~ph_ok],
                   color="tab:red", marker="X", label="Sub-Optimal", **style)
        ax.set_ylabel("pH")
        ax.legend()

        # Bottom-right: dissolved oxygen
        ax = axes[1, 1]
        ax.scatter(time, df_batch.loc[:, "DO_percent"],
                   color="tab:blue", marker="o", **style)
        ax.set_ylabel("Dissolved Oxygen (DO) [%]")

        # Formatting shared by all subplots
        for ax in axes.flat:
            ax.set_xlabel("Time [h]")
            ax.xaxis.set_major_locator(MultipleLocator(6))

        fig.tight_layout()
        fig.savefig(filepath, dpi=300)
        plt.close(fig)

    def export_summary(self, filepath):
        """
        Generates a batch summary table and exports it to a CSV file.

        Parameters
        ----------
        filepath : str
            Output CSV table path.

        Summary Table Columns
        ---------------------
        batch_id
            Batch identifier.

        ph_optimal_percent
            Percentage of measurements in a batch within the
            acceptable pH range, rounded to 2 decimal places.

        temperature_optimal_percent
            Percentage of measurements in a batch within the
            acceptable temperature range, rounded to 2 decimal places.

        C_product_g_L^-1_final
            Final product concentration for the batch.
        """
        records = []
        for batch_id in range(1, self.get_n_batches() + 1):
            df_batch = self.extract_batch(batch_id)
            ph_percent = self.optimal_ph_mask(df_batch).mean() * 100
            temp_percent = self.optimal_temperature_mask(df_batch).mean() * 100
            product_final = df_batch.loc[:, "C_product_g_L^-1"].iloc[-1]
            records.append({
                "batch_id": batch_id,
                "ph_optimal_percent": round(ph_percent, 2),
                "temperature_optimal_percent": round(temp_percent, 2),
                "C_product_g_L^-1_final": product_final,
            })

        df_summary = pd.DataFrame(records)
        df_summary.to_csv(filepath, index=False)