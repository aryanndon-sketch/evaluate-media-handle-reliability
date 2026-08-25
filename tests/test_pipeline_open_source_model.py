import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from pipeline import run_pipeline


class PipelineOpenSourceModelTests(unittest.TestCase):
    @patch("pipeline.OpenSourceBioIdentityModel")
    def test_pipeline_uses_open_source_bio_model_when_enabled(self, model_cls):
        model = model_cls.return_value
        model.predict_identity_clear.return_value = True

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "input.xlsx"
            output_path = tmp / "output.xlsx"
            db_path = tmp / "test.db"

            pd.DataFrame(
                [
                    {
                        "handle": "@example",
                        "platform": "x",
                        "manual_bio_text": "Official account of Example Organization",
                    }
                ]
            ).to_excel(input_path, index=False)

            run_pipeline(
                input_path=input_path,
                output_path=output_path,
                sqlite_path=db_path,
                credible_domains=set(),
                low_credibility_domains=set(),
                factcheck_failed_handles=set(),
                use_open_source_bio_model=True,
            )

            out_df = pd.read_excel(output_path)
            self.assertEqual(out_df.loc[0, "manual_identity_clear"], "yes")
            self.assertEqual(out_df.loc[0, "label"], "neutral")
            self.assertTrue(model.predict_identity_clear.called)


if __name__ == "__main__":
    unittest.main()
