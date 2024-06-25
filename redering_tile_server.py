#! /usr/bin/env python3

# I would like to use FastAPI, but this is not really an API ... isn't it?
# yes! you can say
# @app.get("/{z}/{x}/{y}.{ext}")
# and FastAPI will resolve it for you!

# but

# FastAPI has QUITE some deps: 81MiB in total
# not suitable for a phone, ... but we're not going to run this on a phone, are we? :)

import os.path
import sys

from fastapi import FastAPI, status
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()
# app.root_dir = '.'
app.root_dir = '/home/mdione/src/projects/elevation/Elevation'
# render_farm =


# returning Files requires async
@app.get("/{z}/{x}/{y}.{ext}")
async def get_tile(z: int, x: int, y: int, ext: str):
    # TypeError: join() argument must be str, bytes, or os.PathLike object, not 'int'
    # tile_path = os.path.join(app.root_dir, z, x, f"{y}.{ext}")
    tile_path = f"{app.root_dir}/{z}/{x}/{y}.{ext}"
    if os.path.exists(tile_path):
        return FileResponse(tile_path)

    # beh, it doesn't 404's
    # return FileResponse(tile_path)
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=None)

if __name__ == '__main__':
    app.root_dir = sys.argv[1]
