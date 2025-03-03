import pandas as pd
from sdv.datasets.demo import download_demo
from sdv.multi_table import HMASynthesizer
from sdv.evaluation.multi_table import run_diagnostic, evaluate_quality

class Evaluation:
    """Evaluate synthetic data (ED/HMA) against real data using SDMetrics."""

    def __init__(self, real_data, metadata, dataset_name):
        """
        Initialize the evaluation with real data, metadata, and the dataset name.
        
        Args:
            real_data (dict): Dictionary of real tables.
            metadata (Metadata): SDV metadata for the dataset.
            dataset_name (str): Name of the dataset folder.
        """
        self.real_data = real_data
        self.metadata = metadata
        self.dataset_name = dataset_name
        self.ed_synthetic_data = {}

    def load_ed_synthetic_data(self):
        """
        Load ED synthetic data from CSV files into `self.ed_synthetic_data`.
        Converts ID columns to string type for consistency.
        """
        ed_dir = f"datasets/{self.dataset_name}/ed_data"
        for table_name in self.metadata.to_dict()["tables"].keys():
            csv_path = f"{ed_dir}/{table_name}.csv"
            df = pd.read_csv(csv_path)
            for col, info in self.metadata.to_dict()["tables"][table_name]["columns"].items():
                if info["sdtype"] == "id":
                    df[col] = df[col].astype("object")
                    self.real_data[table_name][col] = self.real_data[table_name][col].astype("object")
            self.ed_synthetic_data[table_name] = df.copy()

    def evaluate(self):
        """
        Evaluate ED and HMA synthetic data by running diagnostics and quality 
        assessments, then save the results to CSV files.
        """
        self._evaluate_ed_method()
        self._evaluate_hma_method()

    def _evaluate_ed_method(self):
        """
        Run diagnostic and quality evaluation on the ED synthetic data,
        then save the results to a CSV file.
        """
        diagnostic = run_diagnostic(self.real_data, self.ed_synthetic_data, self.metadata)
        quality = evaluate_quality(self.real_data, self.ed_synthetic_data, self.metadata)
        self._save_evaluation(diagnostic, quality, "ED")

    def _evaluate_hma_method(self):
        """
        Fit an HMASynthesizer on real data, sample synthetic data, run diagnostics 
        and quality evaluation, then save the results to a CSV file.
        """
        synthesizer = HMASynthesizer(self.metadata)
        synthesizer.fit(self.real_data)
        synthetic_data = synthesizer.sample(scale=0.01)
        diagnostic = run_diagnostic(self.real_data, synthetic_data, self.metadata)
        quality = evaluate_quality(self.real_data, synthetic_data, self.metadata)
        self._save_evaluation(diagnostic, quality, "HMA")

    def _save_evaluation(self, diagnostic, quality, method_name):
        """
        Combine diagnostic and quality results, multiply scores by 100,
        calculate average scores, and save them as a CSV file.
        """
        df_diag = diagnostic.get_properties()
        df_q = quality.get_properties()

        # Multiply scores by 100
        df_diag["Score"] = df_diag["Score"] * 100
        df_q["Score"] = df_q["Score"] * 100

        # Calculate average scores and append
        df_diag.loc[len(df_diag)] = ["Average Total", df_diag["Score"].mean()]
        df_q.loc[len(df_q)] = ["Average Total", df_q["Score"].mean()]

        final_df = pd.concat([df_diag, df_q], ignore_index=True)
        final_df.to_csv(f"datasets/{self.dataset_name}/evaluation/{method_name}.csv", index=False)

if __name__ == "__main__":
    # Set the dataset name to use for the evaluation, it could be 
    # Biodegradability_v1, CORA_v1, DCG_v1 or imdb_MovieLens_v1
    dataset_name = "imdb_MovieLens_v1"
    
    # Download the demo data and metadata for the specified dataset
    real_data, metadata = download_demo(modality="multi_table", dataset_name=dataset_name)
    
    # Create an Evaluation object with the real data, metadata, and dataset name
    evaluator = Evaluation(real_data, metadata, dataset_name)
    
    # Load the ED synthetic data (from CSV files) into the evaluator
    evaluator.load_ed_synthetic_data()
    
    # Perform the evaluation for both ED and HMA methods, then save results
    evaluator.evaluate()