from typing import List, Dict, Union
from .filters import Filter
from types import FunctionType
from .errors import StopPropagation
import json


class Client:

    def __init__(self, addr: str, server, stream=None, session: str = None):
        self.address = addr
        self._server = server
        self._stream = stream
        self.session = session

    async def ban(self):
        self._server.add(self.address)

    async def send(self, packet, close: bool = True):
        payload = packet.payload.encode("utf-8")
        header = packet.length.to_bytes(self._server.header_size, self._server.byteorder)
        data = header + payload
        return await self._server.send_response(self._stream, data, self.session, close)

    async def close(self):
        await self._stream.aclose()


class Packet:

    def __init__(self, fields: Union[Dict[str, str], str, bytes], sender: Client or None):
        self.sender = sender
        if isinstance(fields, dict):
            self.payload = json.dumps(fields)
        elif isinstance(fields, bytes):
            self.payload = json.dumps(json.loads(fields.decode("utf-8")))
        else:
            self.payload = json.dumps(json.loads(fields))
        self.length = len(self.payload)

    async def stop_propagation(self):
        raise StopPropagation


class Handler:

    def __init__(self, function: FunctionType, name: str, filters: List[Filter] = [], priority: int = 0):
        if filters is None:
            filters = []
        self.filters = filters
        self.function = function
        self.name = name
        self.priority = priority

    def __repr__(self):
        return f"Handler({self.function}, '{self.name}', {self.filters}, {self.priority})"

    def compare_names(self, other):
        return other.name == self.name

    def compare_priority(self, other):
        return self.priority == other.priority

    def compare_filters(self, other):
        if len(self.filters) != len(other.filters):
            return False
        for index, filter in enumerate(self.filters):
            ofilter = other.filters[index]
            if ofilter != filter:
                return False
        return True


    def __eq__(self, other):
        if not isinstance(other, Handler):
            raise TypeError(f"The __eq__ operator is meant to compare Handler objects only, not {other}!")
        if other is self:
            return True
        names_equals = self.compare_names(other)
        filters_equals = self.compare_filters(other)
        priority_equals = self.compare_priority(other)
        if names_equals & filters_equals & priority_equals:
            raise RuntimeError("Multiple handlers with identical filters and names cannot share priority level!")
        elif names_equals:
            if not priority_equals:
                if filters_equals:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def call(self, *args):
        return self.function.__call__(*args)

    def __hash__(self):
        return self.function.__name__.__hash__()

class Group:

    def __init__(self, handlers: List[Handler], name: str):
        self.handlers = sorted(handlers, key=lambda x: x.priority)
        self.name = name

    def __repr__(self):
        return f"Group({self.handlers})"

    def __iter__(self):
        return self.handlers.__iter__()




