"""Streamlit Tornado Application module."""

import gc
import logging
import re
from typing import Callable, List, Self, Type

from tornado.routing import PathMatches, Rule
from tornado.web import Application, RequestHandler

# from web.utils.layout import st_app


class StreamlitApplication:
    """returns a reference to the Streamlit instance of the Tornado Application object.

    This uses a hack, grabbing the instance from the garbage collector because Streamlit does not directly expose.
    Source: https://discuss.streamlit.io/t/streamlit-restful-app/409/19?u=janaka
    """

    _rules: List[Rule] = []
    __singleton_instance = None

    # TODO: figure out how to set instance of the class with the Tornado Application object.
    # when the code below returns the instance it overwrites the function we've defined like add_route()
    # def __new__(cls:Type["StreamlitApplication"], *args, **kwargs) -> Any:
    #     """Create a singleton instance and set to the Streamlit Tornado Application object.."""
    #     if not cls.__singleton_instance:
    #         cls.__singleton_instance = super(StreamlitApplication, cls).__new__(cls, *args, **kwargs)
    #         #cls.__singleton_instance = next(o for o in gc.get_referrers(Application) if o.__class__ is Application)
    #     return cls.__singleton_instance

    def get_singleton_instance(self: Self) -> Application:
        """Return the singleton instance of the Streamlit Tornado Application object."""
        if not self.__singleton_instance:
            self.__singleton_instance = next(o for o in gc.get_referrers(Application) if o.__class__ is Application)
        return self.__singleton_instance

    def add_route_handler(self: Self, rule: Rule) -> None:
        """Add a route rule."""
        logging.debug("Adding route handler: %s", rule)
        # self._rules.append(rule)
        tornado_app: Application = self.get_singleton_instance()
        tornado_app.wildcard_router.rules.insert(0, rule)

    # def register_routes(self: Self) -> None:
    #     """Register the routes with the Streamlit Tornado Application instance."""
    #     tornado_app: Application = self.get_singleton_instance()
    #     for rule in self._rules:
    #         if rule not in tornado_app.wildcard_router.rules:
    #             logging.debug("Registering new route: %s",rule)
    #             #tornado_app.wildcard_router.rules.append(rule)
    #             tornado_app.wildcard_router.rules.insert(0,rule)
    #     logging.debug("Registered %s routes with the Streamlit Tornado Application instance.", len(self._rules))

    def api_route(self: Self, path: str) -> Callable[[Type[RequestHandler]], Type[RequestHandler]]:
        """Decorator factory for adding a route to a handler.

        Example:
          ```python

          from typing import Self

          from tornado.web import RequestHandler

          from web.utils.streamlit_application import st_app


          @st_app.api_route("/api/hello")
          class HelloHandler(RequestHandler):
              def get(self: Self) -> None:
                  self.write({"message": "hello world"})
          ```

          With path arguments:
          ```python
          @st_app.api_route("/api/hello/user/{user_id}/name/{name}") // path arg names are just to make reading easier
          class HelloHandler(RequestHandler):
              def get(self: Self, user, name=None) -> None: // the args are passed in the order they appear in the path. 'name' is optional
                  self.write({"message": "hello world"})
          ```

          The above path arguments syntax is replaced with the regex `([^/]{1,150})` as regex is what Tornado uses to match the path.
          Note that the regex we use limits values to 150 characters. This is a security measure to prevent a bad actor from DOSing the server with a very long paths
          cause high memory consumption. Values longer than 150 characters will not match the route and will return a 404.
        """

        def convert_args_in_path_to_regex(path: str) -> str:
            """Convert the path to a regex pattern."""
            # Replace any '{var}' pattern with '([^/]{1,100})'
            regex_path = re.sub(r"\{[^}]+\}", r"([^/]{1,150})", path)
            # Add the raw string indicator 'r' and replace any '/' with '\/'
            regex_path = 'r"' + regex_path.replace("/", r"\/") + '"'
            return regex_path

        path = convert_args_in_path_to_regex(path)

        def decorator(cls: Type[RequestHandler]) -> Type[RequestHandler]:
            logging.debug("Decorator adding route handler: %s", cls)
            self.add_route_handler(Rule(PathMatches(path), cls))
            return cls

        return decorator


st_app = StreamlitApplication()
