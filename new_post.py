import argparse
import os

from datetime import date

ap = argparse.ArgumentParser()
ap.add_argument('title', default='title')
args = ap.parse_args()

POST_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'docs', 'posts', f'{date.today()}-{args.title}')

os.mkdir(POST_DIR)
os.mkdir(os.path.join(POST_DIR, 'assets'))

with open(os.path.join(POST_DIR, 'index.md'), 'w') as index:
    index.write(
f'''---
title: {args.title}
date: {date.today()}
---

![hero image](./assets/hero.jpg)

intro snippet

<!-- more -->

## Header 1


''')
