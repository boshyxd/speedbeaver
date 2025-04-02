from collections.abc import Collection

import structlog
from structlog.processors import CallsiteParameter
from structlog.types import EventDict, Processor


class ProcessorCollectionBuilder:
    def __init__(self):
        self.processors: list[Processor] = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.ExtraAdder(),
            self._drop_color_message_key,
        ]

    def add_logger_name(self) -> "ProcessorCollectionBuilder":
        self.processors.append(structlog.stdlib.add_logger_name)
        return self

    def add_log_level(self) -> "ProcessorCollectionBuilder":
        self.processors.append(structlog.stdlib.add_log_level)
        return self

    def add_positional_arguments(self) -> "ProcessorCollectionBuilder":
        self.processors.append(structlog.stdlib.PositionalArgumentsFormatter())
        return self

    def add_timestamp(
        self, format: str = "iso"
    ) -> "ProcessorCollectionBuilder":
        self.processors.append(structlog.processors.TimeStamper(fmt=format))
        return self

    def add_callsite_parameters(
        self, override: Collection[CallsiteParameter] | None = None
    ) -> "ProcessorCollectionBuilder":
        default_callsite_parameters = {
            structlog.processors.CallsiteParameter.PATHNAME,
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.MODULE,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.THREAD,
            structlog.processors.CallsiteParameter.THREAD_NAME,
            structlog.processors.CallsiteParameter.PROCESS,
            structlog.processors.CallsiteParameter.PROCESS_NAME,
        }
        self.processors.append(
            structlog.processors.CallsiteParameterAdder(
                default_callsite_parameters if override is None else override
            )
        )
        return self

    def add_stack_info_renderer(self) -> "ProcessorCollectionBuilder":
        self.processors.append(structlog.processors.StackInfoRenderer())
        return self

    def add_exception_info(self) -> "ProcessorCollectionBuilder":
        self.processors.append(structlog.processors.format_exc_info)
        return self

    def add_event_key_rename(
        self, to: str = "message", replace_by: str = "_event"
    ) -> "ProcessorCollectionBuilder":
        self.processors.append(
            structlog.processors.EventRenamer(to, replace_by)
        )
        return self

    def _drop_color_message_key(
        self, _, __, event_dict: EventDict
    ) -> EventDict:
        """
        Uvicorn logs the message a second time in the extra `color_message`, but we don't
        need it. This processor drops the key from the event dict if it exists.
        """
        event_dict.pop("color_message", None)
        return event_dict

    def get_processors(self) -> list[Processor]:
        return self.processors
