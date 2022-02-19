# Indoor

## Description
This project is an interoperable software that allows to manage advertising panels all over the world by the addreality instruments.

## Install

```console
git clone this repository.

pip3 install -r requirements.txt
```

## Setup of options

Edit ```./add_reality/default.yaml``` with your DB and server requirements.

Init DB by
```python3 ./add_reality/scripts/utils/db_init.py```

Add platform by
```python3 ./add_reality/scripts/utils/add_publisher.py```


## Run

Open terminal in the project's directory and write the next command:
```python3 ./meta_add/scripts/utils/db_init.py```
