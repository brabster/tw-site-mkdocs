import argparse
import os
import re

from datetime import date

ap = argparse.ArgumentParser()
ap.add_argument('title', default='title')
args = ap.parse_args()

title_filename = f"{date.today()}-{re.sub(r'[ _]', '-', args.title.lower())}"

POST_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'docs', 'posts', f'{title_filename}')

os.mkdir(POST_DIR)
os.mkdir(os.path.join(POST_DIR, 'assets'))

with open(os.path.join(POST_DIR, 'index.md'), 'w') as index:
    index.write(
f'''---
title: {args.title}
date: {date.today()}
---

![hero image](./assets/hero.webp)

intro snippet

--8<-- "ee.md"

<!-- more -->

## Header 1

<figure markdown="span">
 ![template figure](./assets/image.webp)
 <figcaption>template figure</figcaption>
</figure>


--8<-- "blog-feedback.md"

''')
