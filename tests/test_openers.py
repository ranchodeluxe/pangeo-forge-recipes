from pickle import dumps, loads

import pytest
import xarray as xr
from pytest_lazyfixture import lazy_fixture

from pangeo_forge_recipes.openers import open_url, open_with_xarray
from pangeo_forge_recipes.patterns import FileType


@pytest.fixture(
    scope="module",
    params=[
        lazy_fixture("netcdf_local_paths_sequential_1d"),
        lazy_fixture("netcdf_public_http_paths_sequential_1d"),
        lazy_fixture("netcdf_private_http_paths_sequential_1d"),
    ],
    ids=["local", "http-public", "http-private"],
)
def url_and_type(request):
    all_urls, _, _, _, extra_kwargs, type_str = request.param
    kwargs = {
        "secrets": extra_kwargs.get("query_string_secrets", None),
        "open_kwargs": extra_kwargs.get("fsspec_open_kwargs", None),
    }
    file_type = FileType(type_str)
    return all_urls[0], kwargs, file_type


@pytest.fixture(
    scope="module",
    params=[
        lazy_fixture("netcdf_local_paths_sequential_1d"),
    ],
    ids=["local"],
)
def public_url_and_type(request):
    all_urls, _, _, _, _, type_str = request.param
    file_type = FileType(type_str)
    return all_urls[0], file_type


@pytest.fixture(params=[True, False], ids=["with_cache", "no_cache"])
def cache(tmp_cache, request):
    if request.param:
        return tmp_cache
    else:
        return None


def test_open_url(url_and_type, cache):
    url, kwargs, file_type = url_and_type
    if cache:
        assert not cache.exists(url)
    open_file = open_url(url, cache=cache, **kwargs)
    open_file2 = loads(dumps(open_file))
    with open_file as f1:
        data = f1.read()
    with open_file2 as f2:
        data2 = f2.read()
    assert data == data2
    if cache:
        assert cache.exists(url)
        with cache.open(url, mode="rb") as f3:
            data3 = f3.read()
        assert data3 == data


@pytest.fixture(params=[False, True], ids=["lazy", "eager"])
def load(request):
    return request.param


def is_valid_dataset(ds, in_memory=False):
    assert isinstance(ds, xr.Dataset)
    offending_vars = [vname for vname in ds.data_vars if ds[vname].variable._in_memory != in_memory]
    if offending_vars:
        msg = "were NOT in memory" if in_memory else "were in memory"
        raise AssertionError(f"The following vars {msg}: {offending_vars}")


def test_open_file_with_xarray(url_and_type, cache, load):
    # open fsspec OpenFile objects
    url, kwargs, file_type = url_and_type
    open_file = open_url(url, cache=cache, **kwargs)
    ds = open_with_xarray(open_file, file_type=file_type, load=load)
    is_valid_dataset(ds, in_memory=load)


def test_direct_open_with_xarray(public_url_and_type, load):
    # open string URLs
    url, file_type = public_url_and_type
    ds = open_with_xarray(url, file_type=file_type, load=load)
    is_valid_dataset(ds, in_memory=load)
