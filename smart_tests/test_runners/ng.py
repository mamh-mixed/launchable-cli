from . import smart_tests


@smart_tests.subset
def subset(client):
    """
    Input format example:
        src/app/feature/feature.component.spec.ts
        src/app/service/service.service.spec.ts

    Output format: --include=<path> format that can be passed to ng test
    Example:
        --include=src/app/feature/feature.component.spec.ts --include=src/app/service/service.service.spec.ts
    """
    for t in client.stdin():
        path = t.strip()
        if path:
            client.test_path(path)

    client.formatter = lambda x: "--include={}".format(x[0]['name'])
    client.separator = " "
    client.run()
