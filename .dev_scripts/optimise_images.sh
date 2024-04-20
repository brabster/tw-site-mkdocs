#!/bin/bash

set -euo pipefail

resize_and_webp () {
    local image_path=${1}
    local size=(`identify -format '%w %h' ${image_path}`)
    echo $size
    local maybe_resize_arg=''

    if [ ${size[0]} -gt 1024 ]; then
        maybe_resize_arg=" -resize 1024 0 "
    fi

    cwebp -q 60 ${maybe_resize_arg} -mt "${image_path}" -o ${image_path%.*}.webp
}

for image_path in $(find docs -name *.png); do
    resize_and_webp "${image_path}"
done

for image_path in $(find docs -name *.jpg); do
    resize_and_webp "${image_path}"
done

