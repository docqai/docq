# Extensions (alpha)

Note: this interface is highly unstable. Expect breaking changes.

Extensions is a type of plugin system that enables you to extend Docq functionality. This enables developing custom extensions as external modules. Then add to Docq through configuration (so imported dynamically at build time or run).

An extension is a Python _module_ that implement one of the `DocqExtension` interface (that is inherits from):

- `DocqWebUiExtension` - Web UI extensions
- `DocqWebApiExtension` - Web API extensions (in the future as there's no web API at present)
- `DocqDalExtension` - Database layer extensions

Docq implements extensions as a event hooks system. In places that can be extended Docq fires the `callback_handler()` method on all registered extensions. The `event_name` is used identify which hook was fired. Together with `ExtensionContext` allows implementing logic.

## Configure Docq Extensions

Drop a `.docq-extensions.json` file into the root folder of the Docq app deployment. In the future we'll develop an easier way to deploy extensions without having to redeploy the entire Docq app.

Any custom modules that are imported within an extension also needs to be added to `.docq-extensions.json`. Otherwise you will get import errors when the using module is being loaded and registered during Docq initialisation.

## `.docq-extensions.json` Schema

```json
{
  "unique_key": {
    "name": "any friendly name",
    "module_name": "<the full qualified module path. Same as `from` in an static import",
    "source": "<location of the source. Relative path (or git url in the future)",
    "class_name": "<(optional) name of your class that inherits from `DocqExtension`"
  }
}
```

Example:

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

## Deploying Extensions

In the above example, relative paths is based on the extension package source code living in a sibling folder to Docq.

``` md

- workspace
  - docq-repo
    - source/docq
    - web
    - .docq-extensions.json
  - docq-extension-repo
    - source
      - docq
      - web
```

When Docq is deployed same relative folder structure should be maintained for the above example `.docq-extensions.json` to work. Otherwise adjust relative paths for source.

The build step must perform a `poetry install` to install third-party dependencies used by the extensions package.

## Developing Extensions

Details on local dev workflow coming soon.
