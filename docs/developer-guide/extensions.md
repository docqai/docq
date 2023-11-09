# Extensions (alpha)

Note: this interface is highly unstable. Expect breaking changes.

Extensions is a type of plugin system that enables you to extend Docq functionality. This enables developing custom extensions as external modules. Then add to Docq through configuration (so imported dynamically at build time or run).

Extensions are Python modules that implement one of the `DocqExtension` classes:

- `DocqWebUiExtension` - Web UI extensions
- `DocqWebApiExtension` - Web API extensions (in the future as there's no web API at present)
- `DocqDalExtension` - Database layer extensions

Docq implements extensions as a event hooks system. In places that can be extended Docq fires the `callback_handler()` method on all registered extensions. The `event_name` is used identify which hook was fired. Together with `ExtensionContext` allows implementing logic.

## Configure Docq Extensions

Drop a `.docq-extensions.json` file into the root folder of the Docq app deployment. In the future we'll develop easier way to deploy extensions without having to redeploy the entire Docq app.

## `.docq-extensions.json` Schema

```json
{
  "unique_key": {
    "name": "any friendly name",
    "module_name": "<the full module path. Same as `from` in an static import",
    "source": "<location of the source. Relative path or git url",
    "class_name": "<name of your class that inherits from `DocqExtension`"
  }
}
```

Example

```json
{
  "docq_extensions.web.layout.example": {
    "name": "Docq example web extension",
    "module_name": "docq_extensions.web.layout.example",
    "source": "../docq-extensions/source/docq_extensions/web/layout/example.py",
    "class_name": "Example"
  },
  "docq_extensions.web.layout.example_dal": {
    "name": "Docq example DAL extension",
    "module_name": "docq_extensions.docq.example_dal",
    "source": "../docq-extensions/source/docq_extensions/docq/example_dal.py",
    "class_name": "ExampleDal"
  }
}
```


