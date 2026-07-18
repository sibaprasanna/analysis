import re

COLUMN_MAPPING = {

    "recipient_email": [
        "rcpt",
        "recipient",
        "recipient email",
        "recipient address",
        "email address",
        "to"
    ],

    "sender_email": [
        "orig",
        "sender",
        "from"
    ],

    "dsn_status": [
        "dsnstatus"
    ],

    "message_id": [
        "messageid",
        "message id"
    ],

    "subject": [
        "subject"
    ]
}


def normalize(text):

    return re.sub(
        r'[^a-z0-9]',
        '',
        text.lower()
    )


def map_columns(df):

    rename_dict = {}

    for column in df.columns:

        normalized_column = normalize(column)

        for standard_name, aliases in COLUMN_MAPPING.items():

            for alias in aliases:

                if normalize(alias) == normalized_column:

                    rename_dict[column] = standard_name
                    break

    return df.rename(columns=rename_dict)