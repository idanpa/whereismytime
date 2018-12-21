# Where is my time? ⌚
Find out where is your time. Simple time management CLI.

## Installation
```bash
pip install wmt
```

On first usage you will be asked to configure your setup. Supported configuration are using local .csv file or hosting it automatically on OneDrive.

## Usage

```bash
$ wmt start -n project_a,task_b,initial_work
$ wmt end
```

```bash
$ wmt start -n project_b,task_c -t "yesterday at 10:00"
$ wmt end -t "yesterday at 12:15"
```

or you can just use `wmt`, it would start a session and end it if it found a running session:

```
$ wmt
Please type session name:project x, task 2
project x, task 2 2018-12-21 13:05:42
$ wmt
project x, task 2 ended (45 minutes)
```
