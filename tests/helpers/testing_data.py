import pandas as pd

transformed_data = pd.DataFrame(
        {
            'cr_id': ["1008899", "1087378", "1087387", "1087308", "1008913"],
            'beat_id': [260, 249, 209, 48, 173]
        }
    ).astype({'beat_id': "Int32"})
