"""
Create sandbox environment for running untrasted code.

Should we trust LLMs that they would not accidentally delete our OS?
"""

from datetime import datetime
from pathlib import Path
from typing import NamedTuple

import asyncio
import docker
import io
import tarfile
import uuid


class File(NamedTuple):
    """File for a docker container."""

    path: Path
    data: str | bytes


class Dockerfile(NamedTuple):
    """
    Dockerfile representation.

    Structure of the dockerfile:
    ```
    FROM {image}

    RUN {run[0]}
    RUN {run[1]}
    ...
    RUN {run[n]}

    RUN adduser -m {user}
    USER {user}
    WORKDIR /home/{user}

    [automatically generated code for file copy]
    RUN mkdir -p {path without filename}
    COPY {path} .

    ENTRYPOINT [{"x" for x in exec}]
    ```
    """
    image: str
    user: str
    run: tuple[str, ...]
    exec: tuple[str, ...]

    def stringify(self, files: tuple[File, ...]) -> str:
        """Create string representation of dockerfile."""
        copy_files = '\n'.join(f'RUN mkdir -p {file.path.parent}\n'
                               f'COPY {file.path} {file.path.parent}'
                               for file in files)
        entrypoint = ', '.join(f'"{x}"' for x in self.exec)
        return (f'FROM {self.image}\n\n'
                + '\n'.join(f'RUN {x}' for x in self.run) + '\n\n'
                + f'RUN useradd -m {self.user}\n'
                + f'USER {self.user}\n'
                + f'WORKDIR /home/{self.user}\n\n'
                + copy_files + '\n'
                + f'ENTRYPOINT [{entrypoint}]')


class Record(NamedTuple):
    """Result of the docker container run."""

    status_code: int
    build_logs: tuple[str, ...]
    run_logs: str
    workspace: Path
    files: dict[Path, bytes]


def namefy(name: str, *, add_time: bool = True, add_uuid: bool = True) -> str:
    """Create valid container name with minimal chance for name collisions."""
    time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f') if add_time else ''
    return (f'{name}_{time}_{uuid.uuid4() if add_uuid else ""}').lower()


def _run(name: str,
         subfolder: Path,
         dockerfile: Dockerfile,
         *,
         add_files: tuple[File, ...] = (),
         get_files: tuple[Path, ...] = ()
         ) -> Record:
    client = docker.from_env()
    workspace = subfolder / name
    workspace.mkdir(parents=True, exist_ok=False)

    (workspace / 'Dockerfile').write_text(dockerfile.stringify(add_files))

    assert not any(x.path.is_absolute() for x in add_files)
    for file in add_files:
        path = workspace / file.path
        path.parent.mkdir(parents=True, exist_ok=True)
        match file.data:
            case str():
                path.write_text(file.data)
            case bytes():
                path.write_bytes(file.data)

    _, _build_logs = client.images.build(path=str(workspace.resolve()),
                                         tag=name)
    build_logs = tuple((log if isinstance(log, dict) else {}).get('stream', '')
                       for log in _build_logs)

    container = client.containers.run(name, detach=True)

    try:
        result = container.wait()
        container.start()

        status_code = result['StatusCode']
        logs = container.logs().decode()

        files = {}
        assert all(path.is_absolute() for path in get_files)
        for path in get_files:
            code, _ = container.exec_run(f'test -f {path}',
                                         stdout=False,
                                         stderr=False)

            if code != 0:
                print(code)
                continue

            archive, _ = container.get_archive(str(path))
            data = io.BytesIO(b''.join(archive))
            with tarfile.open(fileobj=data) as tar:
                if file := tar.extractfile(tar.getmember(path.name)):
                    files[path] = file.read()

        return Record(status_code=status_code,
                      build_logs=build_logs,
                      run_logs=logs,
                      workspace=workspace,
                      files=files)
    finally:
        container.stop()
        container.remove()


async def run(name: str,
              subfolder: Path,
              dockerfile: Dockerfile,
              *,
              add_files: tuple[File, ...] = (),
              get_files: tuple[Path, ...] = ()
              ) -> Record:
    """
    Create docker image with a given name, run it and return its result.

    The image workspace will bu created in `subfolder` and will contain all
    the file specified by `add_files`. Loaded files from image after the
    end of entrypoint can be specified using `get_files`.
    """
    return await asyncio.to_thread(_run,
                                   name,
                                   subfolder,
                                   dockerfile,
                                   add_files=add_files,
                                   get_files=get_files)
