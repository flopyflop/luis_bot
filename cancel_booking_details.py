class CancelBookingDetails:
    def __init__(
        self,
        destination: str = None,
        travel_date: str = None,
        unsupported_airports=None,
        user_id=-1
    ):
        if unsupported_airports is None:
            unsupported_airports = []
        self.destination = destination
        self.travel_date = travel_date
        self.unsupported_airports = unsupported_airports
        self.user_id = user_id