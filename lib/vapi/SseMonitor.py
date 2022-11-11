import json
import logging as logger


class SseMonitor:
    """
    SseMonitor is different than other VAPI resources. It can only report SSEs.
    Reporting uses streaming so as each SSE is received, it is 'yielded' to the
    caller.
    """

    def __init__(self, server):
        self.server = server

    def report(self, includeEvents: list = None, excludeEvents: list = None):
        """
        Streams the 'data' part of event's whose name matches the input name, or all events if no name is provided.

        :param: includeEvents -- list of event names to include in the result stream.
        :param: excludeEvents -- list of event names to specifically exclude from the result stream

        :returns: returns a stream of dicts representing the SSE (note if data is json, it is loaded as a dictionary)
        """
        uri = "/events"
        self.server.get(uri, stream=True)

        fieldSeparator = ":"
        validFieldNames = ["event", "data"]

        for sseString in self.readWholeEvent(self.server.raw_rsp()):
            sse = {}
            for line in sseString.splitlines():
                line = line.decode("utf-8")

                # skip blank lines and lines with no field name (aka key).
                # This should never happen with MVI, but empty strings cause problems for 'split()'
                if not line.strip() or line.startswith(fieldSeparator):
                    continue

                field, value = line.split(fieldSeparator, 1)

                # log unknown fields, but otherwise ignore them
                if field not in validFieldNames:
                    logger.debug(f"Got field '{field}', but expected one of '{validFieldNames}'.")

                value = value.strip()
                # Try to return 'data' value as json if possible.
                if field == "data":
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError as exc:
                        logger.debug(f"Could not decode SSE data as json -- {exc}")
                sse[field] = value

            # Dispatch the SSE
            event = sse["event"]
            if (excludeEvents is not None and event in excludeEvents) or \
               (includeEvents is not None and event not in includeEvents):
                logger.warning(f"""@@@ skipping SSE '{event}'; exclude={excludeEvents}, include={includeEvents}""")
            else:
                yield sse

    def readWholeEvent(self, sseStream):
        """
        Reads an entire SSE event using various combination of 2 newlines as the terminator.

        :returns: SSE as a string
        """
        sse = b''
        for data in sseStream:
            for line in data.splitlines(True):
                sse += line
                if sse.endswith((b'\r\r', b'\n\n', b'\r\n\r\n')):
                    yield sse
                    sse = b''
        if sse:
            yield sse


