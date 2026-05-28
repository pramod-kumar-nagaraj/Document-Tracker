class Document:
    def __init__(
        self,
        name,
        category,
        start_date,
        expiry_date,
        reminder_days,
        notes,
    ):
        self.name = name
        self.category = category
        self.start_date = start_date
        self.expiry_date = expiry_date
        self.reminder_days = reminder_days
        self.notes = notes