# Daniel (UK) Text To Speech API

Implementation of an API that runs on OSX that serves the high quality Daniel voice that ships with Macs. Existing voices that work with SAPI5 on windows have much worse quality. 

## Prerequisites

Only works on macs. Download the higher quality Daniel voice in accessibility settings.

Pipenv is also needed for dependency installation.

## Installation

```
$ pipenv install
$ pipenv shell
$ uvicorn app:app --reload --host 0.0.0.0 --port 6969
```

