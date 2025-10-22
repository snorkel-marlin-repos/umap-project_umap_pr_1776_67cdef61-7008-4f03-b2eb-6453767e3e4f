import json
import platform
import re
from pathlib import Path
from time import sleep

import pytest
from playwright.sync_api import expect

from umap.models import DataLayer

pytestmark = pytest.mark.django_db


def test_layers_list_is_updated(live_server, tilelayer, page):
    page.goto(f"{live_server.url}/map/new/")
    modifier = "Cmd" if platform.system() == "Darwin" else "Ctrl"
    page.get_by_role("link", name=f"Import data ({modifier}+I)").click()
    # Should work
    page.get_by_label("Choose the layer to import").select_option(
        label="Import in a new layer"
    )
    page.get_by_role("link", name="Manage layers").click()
    page.get_by_role("button", name="Add a layer").click()
    page.locator('input[name="name"]').click()
    page.locator('input[name="name"]').fill("foobar")
    page.get_by_role("link", name=f"Import data ({modifier}+I)").click()
    # Should still work
    page.get_by_label("Choose the layer to import").select_option(
        label="Import in a new layer"
    )
    # Now layer should be visible in the options
    page.get_by_label("Choose the layer to import").select_option(label="foobar")


def test_umap_import_from_file(live_server, tilelayer, page):
    page.goto(f"{live_server.url}/map/new/")
    page.get_by_title("Import data").click()
    file_input = page.locator("input[type='file']")
    with page.expect_file_chooser() as fc_info:
        file_input.click()
    file_chooser = fc_info.value
    path = Path(__file__).parent.parent / "fixtures/display_on_load.umap"
    file_chooser.set_files(path)
    button = page.get_by_role("button", name="Import", exact=True)
    expect(button).to_be_visible()
    button.click()
    assert file_input.input_value()
    # Close the import panel
    page.keyboard.press("Escape")
    # Reopen
    page.get_by_title("Import data").click()
    sleep(1)  # Wait for CSS transition to happen
    assert not file_input.input_value()
    expect(page.locator(".umap-main-edit-toolbox .map-name")).to_have_text(
        "Carte sans nom"
    )
    page.get_by_title("See layers").click()
    layers = page.locator(".umap-browser .datalayer")
    expect(layers).to_have_count(2)
    nonloaded = page.locator(".umap-browser .datalayer.off")
    expect(nonloaded).to_have_count(1)


def test_umap_import_from_textarea(live_server, tilelayer, page, settings):
    settings.UMAP_ALLOW_ANONYMOUS = True
    page.goto(f"{live_server.url}/map/new/")
    page.get_by_role("button", name="See layers").click()
    page.get_by_title("Import data").click()
    textarea = page.locator(".umap-upload textarea")
    path = Path(__file__).parent.parent / "fixtures/test_upload_data.umap"
    textarea.fill(path.read_text())
    page.locator('select[name="format"]').select_option("umap")
    page.get_by_role("button", name="Import", exact=True).click()
    layers = page.locator(".umap-browser .datalayer")
    expect(layers).to_have_count(2)
    expect(page.locator(".umap-main-edit-toolbox .map-name")).to_have_text(
        "Imported map"
    )
    expect(page.get_by_text("Tunnels")).to_be_visible()
    expect(page.get_by_text("Cities")).to_be_visible()
    expect(page.locator(".leaflet-control-minimap")).to_be_visible()
    expect(
        page.locator('img[src="https://tile.openstreetmap.fr/hot/6/32/21.png"]')
    ).to_be_visible()
    # Should not have imported umap_id, while in the file options
    assert not page.evaluate("U.MAP.options.umap_id")
    with page.expect_response(re.compile(r".*/datalayer/create/.*")):
        page.get_by_role("button", name="Save").click()
    assert page.evaluate("U.MAP.options.umap_id")


def test_import_geojson_from_textarea(tilelayer, live_server, page):
    page.goto(f"{live_server.url}/map/new/")
    page.get_by_title("See layers").click()
    layers = page.locator(".umap-browser .datalayer")
    markers = page.locator(".leaflet-marker-icon")
    paths = page.locator("path")
    expect(markers).to_have_count(0)
    expect(paths).to_have_count(0)
    expect(layers).to_have_count(0)
    button = page.get_by_title("Import data")
    expect(button).to_be_visible()
    button.click()
    textarea = page.locator(".umap-upload textarea")
    path = Path(__file__).parent.parent / "fixtures/test_upload_data.json"
    textarea.fill(path.read_text())
    page.locator('select[name="format"]').select_option("geojson")
    button = page.get_by_role("button", name="Import", exact=True)
    expect(button).to_be_visible()
    button.click()
    # A layer has been created
    expect(layers).to_have_count(1)
    expect(markers).to_have_count(2)
    expect(paths).to_have_count(3)


def test_import_kml_from_textarea(tilelayer, live_server, page):
    page.goto(f"{live_server.url}/map/new/")
    page.get_by_title("See layers").click()
    layers = page.locator(".umap-browser .datalayer")
    markers = page.locator(".leaflet-marker-icon")
    paths = page.locator("path")
    expect(markers).to_have_count(0)
    expect(paths).to_have_count(0)
    expect(layers).to_have_count(0)
    button = page.get_by_title("Import data")
    expect(button).to_be_visible()
    button.click()
    textarea = page.locator(".umap-upload textarea")
    path = Path(__file__).parent.parent / "fixtures/test_upload_data.kml"
    textarea.fill(path.read_text())
    page.locator('select[name="format"]').select_option("kml")
    button = page.get_by_role("button", name="Import", exact=True)
    expect(button).to_be_visible()
    button.click()
    # A layer has been created
    expect(layers).to_have_count(1)
    expect(markers).to_have_count(1)
    expect(paths).to_have_count(2)


def test_import_gpx_from_textarea(tilelayer, live_server, page):
    page.goto(f"{live_server.url}/map/new/")
    page.get_by_title("See layers").click()
    layers = page.locator(".umap-browser .datalayer")
    markers = page.locator(".leaflet-marker-icon")
    paths = page.locator("path")
    expect(markers).to_have_count(0)
    expect(paths).to_have_count(0)
    expect(layers).to_have_count(0)
    button = page.get_by_title("Import data")
    expect(button).to_be_visible()
    button.click()
    textarea = page.locator(".umap-upload textarea")
    path = Path(__file__).parent.parent / "fixtures/test_upload_data.gpx"
    textarea.fill(path.read_text())
    page.locator('select[name="format"]').select_option("gpx")
    button = page.get_by_role("button", name="Import", exact=True)
    expect(button).to_be_visible()
    button.click()
    # A layer has been created
    expect(layers).to_have_count(1)
    expect(markers).to_have_count(1)
    expect(paths).to_have_count(1)


def test_import_osm_from_textarea(tilelayer, live_server, page):
    page.goto(f"{live_server.url}/map/new/")
    page.get_by_title("See layers").click()
    layers = page.locator(".umap-browser .datalayer")
    markers = page.locator(".leaflet-marker-icon")
    expect(markers).to_have_count(0)
    expect(layers).to_have_count(0)
    button = page.get_by_title("Import data")
    expect(button).to_be_visible()
    button.click()
    textarea = page.locator(".umap-upload textarea")
    path = Path(__file__).parent.parent / "fixtures/test_upload_data_osm.json"
    textarea.fill(path.read_text())
    page.locator('select[name="format"]').select_option("osm")
    page.get_by_role("button", name="Import", exact=True).click()
    # A layer has been created
    expect(layers).to_have_count(1)
    expect(markers).to_have_count(2)


def test_import_csv_from_textarea(tilelayer, live_server, page):
    page.goto(f"{live_server.url}/map/new/")
    page.get_by_title("See layers").click()
    layers = page.locator(".umap-browser .datalayer")
    markers = page.locator(".leaflet-marker-icon")
    expect(markers).to_have_count(0)
    expect(layers).to_have_count(0)
    button = page.get_by_title("Import data")
    expect(button).to_be_visible()
    button.click()
    textarea = page.locator(".umap-upload textarea")
    path = Path(__file__).parent.parent / "fixtures/test_upload_data.csv"
    textarea.fill(path.read_text())
    page.locator('select[name="format"]').select_option("csv")
    page.get_by_role("button", name="Import", exact=True).click()
    # A layer has been created
    expect(layers).to_have_count(1)
    expect(markers).to_have_count(2)


def test_can_import_in_existing_datalayer(live_server, datalayer, page, openmap):
    page.goto(f"{live_server.url}{openmap.get_absolute_url()}")
    page.get_by_title("See layers").click()
    layers = page.locator(".umap-browser .datalayer")
    markers = page.locator(".leaflet-marker-icon")
    expect(markers).to_have_count(1)
    expect(layers).to_have_count(1)
    page.get_by_role("button", name="Edit").click()
    page.get_by_title("Import data").click()
    textarea = page.locator(".umap-upload textarea")
    path = Path(__file__).parent.parent / "fixtures/test_upload_data.csv"
    textarea.fill(path.read_text())
    page.locator('select[name="format"]').select_option("csv")
    page.get_by_role("button", name="Import", exact=True).click()
    # No layer has been created
    expect(layers).to_have_count(1)
    expect(markers).to_have_count(3)


def test_can_replace_datalayer_data(live_server, datalayer, page, openmap):
    page.goto(f"{live_server.url}{openmap.get_absolute_url()}")
    page.get_by_title("See layers").click()
    layers = page.locator(".umap-browser .datalayer")
    markers = page.locator(".leaflet-marker-icon")
    expect(markers).to_have_count(1)
    expect(layers).to_have_count(1)
    page.get_by_role("button", name="Edit").click()
    page.get_by_title("Import data").click()
    textarea = page.locator(".umap-upload textarea")
    path = Path(__file__).parent.parent / "fixtures/test_upload_data.csv"
    textarea.fill(path.read_text())
    page.locator('select[name="format"]').select_option("csv")
    page.get_by_label("Replace layer content").check()
    page.get_by_role("button", name="Import", exact=True).click()
    # No layer has been created
    expect(layers).to_have_count(1)
    expect(markers).to_have_count(2)


def test_can_import_in_new_datalayer(live_server, datalayer, page, openmap):
    page.goto(f"{live_server.url}{openmap.get_absolute_url()}")
    page.get_by_title("See layers").click()
    layers = page.locator(".umap-browser .datalayer")
    markers = page.locator(".leaflet-marker-icon")
    expect(markers).to_have_count(1)
    expect(layers).to_have_count(1)
    page.get_by_role("button", name="Edit").click()
    page.get_by_title("Import data").click()
    textarea = page.locator(".umap-upload textarea")
    path = Path(__file__).parent.parent / "fixtures/test_upload_data.csv"
    textarea.fill(path.read_text())
    page.locator('select[name="format"]').select_option("csv")
    page.get_by_label("Choose the layer to import").select_option(
        label="Import in a new layer"
    )
    page.get_by_role("button", name="Import", exact=True).click()
    # A new layer has been created
    expect(layers).to_have_count(2)
    expect(markers).to_have_count(3)


def test_should_remove_dot_in_property_names(live_server, page, settings, tilelayer):
    settings.UMAP_ALLOW_ANONYMOUS = True
    data = {
        "type": "FeatureCollection",
        "features": [
            {
                "geometry": {
                    "type": "Point",
                    "coordinates": [6.922931671142578, 47.481161607175736],
                },
                "type": "Feature",
                "properties": {
                    "color": "",
                    "name": "Chez Rémy",
                    "A . in the name": "",
                },
            },
            {
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [2.4609375, 48.88639177703194],
                        [2.48291015625, 48.76343113791796],
                        [2.164306640625, 48.719961222646276],
                    ],
                },
                "type": "Feature",
                "properties": {"color": "", "name": "Périf", "with a dot.": ""},
            },
        ],
    }
    page.goto(f"{live_server.url}/map/new/")
    page.get_by_title("Import data").click()
    textarea = page.locator(".umap-upload textarea")
    textarea.fill(json.dumps(data))
    page.locator('select[name="format"]').select_option("geojson")
    page.get_by_role("button", name="Import", exact=True).click()
    with page.expect_response(re.compile(r".*/datalayer/create/.*")):
        page.get_by_role("button", name="Save").click()
    datalayer = DataLayer.objects.last()
    saved_data = json.loads(Path(datalayer.geojson.path).read_text())
    assert saved_data["features"][0]["properties"] == {
        "color": "",
        "name": "Chez Rémy",
        "A _ in the name": "",
    }
    assert saved_data["features"][1]["properties"] == {
        "color": "",
        "name": "Périf",
        "with a dot_": "",
    }


def test_import_geometry_collection(live_server, page, tilelayer):
    data = {
        "type": "GeometryCollection",
        "geometries": [
            {"type": "Point", "coordinates": [-80.6608, 35.0493]},
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-80.6645, 35.0449],
                        [-80.6634, 35.0460],
                        [-80.6625, 35.0455],
                        [-80.6638, 35.0442],
                        [-80.6645, 35.0449],
                    ]
                ],
            },
            {
                "type": "LineString",
                "coordinates": [
                    [-80.66237, 35.05950],
                    [-80.66269, 35.05926],
                    [-80.66284, 35.05893],
                    [-80.66308, 35.05833],
                    [-80.66385, 35.04387],
                    [-80.66303, 35.04371],
                ],
            },
        ],
    }
    page.goto(f"{live_server.url}/map/new/")
    page.get_by_title("See layers").click()
    layers = page.locator(".umap-browser .datalayer")
    markers = page.locator(".leaflet-marker-icon")
    paths = page.locator("path")
    expect(markers).to_have_count(0)
    expect(paths).to_have_count(0)
    expect(layers).to_have_count(0)
    button = page.get_by_title("Import data")
    expect(button).to_be_visible()
    button.click()
    textarea = page.locator(".umap-upload textarea")
    textarea.fill(json.dumps(data))
    page.locator('select[name="format"]').select_option("geojson")
    page.get_by_role("button", name="Import", exact=True).click()
    # A layer has been created
    expect(layers).to_have_count(1)
    expect(markers).to_have_count(1)
    expect(paths).to_have_count(2)


def test_import_multipolygon(live_server, page, tilelayer):
    data = {
        "type": "Feature",
        "properties": {"name": "Some states"},
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [[-109, 36], [-109, 40], [-102, 37], [-109, 36]],
                    [[-108, 39], [-107, 37], [-104, 37], [-108, 39]],
                ],
                [[[-119, 42], [-120, 39], [-114, 41], [-119, 42]]],
            ],
        },
    }
    page.goto(f"{live_server.url}/map/new/")
    page.get_by_title("See layers").click()
    layers = page.locator(".umap-browser .datalayer")
    paths = page.locator("path")
    expect(paths).to_have_count(0)
    expect(layers).to_have_count(0)
    button = page.get_by_title("Import data")
    expect(button).to_be_visible()
    button.click()
    textarea = page.locator(".umap-upload textarea")
    textarea.fill(json.dumps(data))
    page.locator('select[name="format"]').select_option("geojson")
    page.get_by_role("button", name="Import", exact=True).click()
    # A layer has been created
    expect(layers).to_have_count(1)
    expect(paths).to_have_count(1)


def test_import_multipolyline(live_server, page, tilelayer):
    data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [[[-108, 46], [-113, 43]], [[-112, 45], [-115, 44]]],
                },
            }
        ],
    }
    page.goto(f"{live_server.url}/map/new/")
    page.get_by_title("See layers").click()
    layers = page.locator(".umap-browser .datalayer")
    paths = page.locator("path")
    expect(paths).to_have_count(0)
    expect(layers).to_have_count(0)
    button = page.get_by_title("Import data")
    expect(button).to_be_visible()
    button.click()
    textarea = page.locator(".umap-upload textarea")
    textarea.fill(json.dumps(data))
    page.locator('select[name="format"]').select_option("geojson")
    page.get_by_role("button", name="Import", exact=True).click()
    # A layer has been created
    expect(layers).to_have_count(1)
    expect(paths).to_have_count(1)


def test_import_csv_without_valid_latlon_headers(tilelayer, live_server, page):
    page.goto(f"{live_server.url}/map/new/")
    page.get_by_title("See layers").click()
    layers = page.locator(".umap-browser .datalayer")
    markers = page.locator(".leaflet-marker-icon")
    page.get_by_title("Import data").click()
    textarea = page.locator(".umap-upload textarea")
    textarea.fill("a,b,c\n12.23,48.34,mypoint\n12.23,48.34,mypoint2")
    page.locator('select[name="format"]').select_option("csv")
    page.get_by_role("button", name="Import", exact=True).click()
    # FIXME do not create a layer
    expect(layers).to_have_count(1)
    expect(markers).to_have_count(0)
    expect(page.locator('umap-alert div[data-level="error"]')).to_be_visible()
