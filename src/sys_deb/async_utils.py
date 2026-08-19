import asyncio

def autorun(fn):
    return asyncio.create_task(fn)
