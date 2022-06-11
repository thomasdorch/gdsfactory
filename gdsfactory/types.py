"""In programming, a factory is a function that returns an object.

Functions are easy to understand because they have clear inputs and outputs.
Most gdsfactory functions take some inputs and return a Component object.
Some of these inputs parameters are also functions.

- Component: Object with.
    - name.
    - references: to other components (x, y, rotation).
    - polygons in different layers.
    - ports dict.
- Route: dataclass with 3 attributes.
    - references: list of references (straights, bends and tapers).
    - ports: dict(input=PortIn, output=PortOut).
    - length: how long is this route?

Factories:

- ComponentFactory: function that returns a Component.
- RouteFactory: function that returns a Route.


Specs:

- ComponentSpec: Component, ComponentFactory or dict(component=mzi, settings=dict(delta_length=20)).
- LayerSpec: (3, 0), 3 (asumes 0 as datatype) or string.

"""
import json
import pathlib
from typing import Any, Callable, Dict, List, NewType, Optional, Tuple, Union

import numpy as np
from omegaconf import OmegaConf
from phidl.device_layout import Label as LabelPhidl
from phidl.device_layout import Path
from pydantic import BaseModel, Extra
from typing_extensions import Literal

from gdsfactory.component import Component, ComponentReference
from gdsfactory.cross_section import CrossSection
from gdsfactory.port import Port

Anchor = Literal[
    "ce",
    "cw",
    "nc",
    "ne",
    "nw",
    "sc",
    "se",
    "sw",
    "center",
    "cc",
]
Axis = Literal["x", "y"]

NSEW = Literal["N", "S", "E", "W"]


class Label(LabelPhidl):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        """check with pydantic Label valid type"""
        assert isinstance(v, LabelPhidl), f"TypeError, Got {type(v)}, expecting Label"
        return v


Float2 = Tuple[float, float]
Float3 = Tuple[float, float, float]
Floats = Tuple[float, ...]
Strs = Tuple[str, ...]
Int2 = Tuple[int, int]
Int3 = Tuple[int, int, int]
Ints = Tuple[int, ...]

Layer = Tuple[int, int]
Layers = Tuple[Layer, ...]
LayerSpec = NewType("LayerSpec", Union[Layer, int, str, None])
LayerSpecs = Tuple[LayerSpec, ...]
ComponentFactory = Callable[..., Component]
ComponentFactoryDict = Dict[str, ComponentFactory]
PathFactory = Callable[..., Path]
PathType = Union[str, pathlib.Path]
PathTypes = Tuple[PathType, ...]

ComponentOrPath = Union[PathType, Component]
ComponentOrReference = Union[Component, ComponentReference]
NameToFunctionDict = Dict[str, ComponentFactory]
Number = Union[float, int]
Coordinate = Tuple[float, float]
Coordinates = Tuple[Coordinate, ...]
ComponentOrPath = Union[Component, PathType]
CrossSectionFactory = Callable[..., CrossSection]
CrossSectionOrFactory = Union[CrossSection, Callable[..., CrossSection]]
PortSymmetries = Dict[str, Dict[str, List[str]]]
PortsDict = Dict[str, Port]
PortsList = Dict[str, Port]

ComponentSpec = NewType(
    "ComponentSpec", Union[str, ComponentFactory, Component, Dict[str, Any]]
)
ComponentSpecOrList = Union[ComponentSpec, List[ComponentSpec]]
CellSpec = Union[str, ComponentFactory, Dict[str, Any]]
ComponentSpecDict = Dict[str, ComponentSpec]
CrossSectionSpec = NewType(
    "CrossSectionSpec", Union[str, CrossSectionFactory, CrossSection, Dict[str, Any]]
)
MultiCrossSectionAngleSpec = List[Tuple[CrossSectionSpec, Tuple[int, ...]]]


class Route(BaseModel):
    references: List[ComponentReference]
    labels: Optional[List[Label]] = None
    ports: Tuple[Port, Port]
    length: float

    class Config:
        extra = Extra.forbid


class Routes(BaseModel):
    references: List[ComponentReference]
    lengths: List[float]
    ports: Optional[List[Port]] = None
    bend_radius: Optional[List[float]] = None

    class Config:
        extra = Extra.forbid


class ComponentModel(BaseModel):
    component: Union[str, Dict[str, Any]]
    settings: Optional[Dict[str, Any]]

    class Config:
        extra = Extra.forbid


class PlacementModel(BaseModel):
    x: Union[str, float] = 0
    y: Union[str, float] = 0
    xmin: Optional[Union[str, float]] = None
    ymin: Optional[Union[str, float]] = None
    xmax: Optional[Union[str, float]] = None
    ymax: Optional[Union[str, float]] = None
    dx: float = 0
    dy: float = 0
    port: Optional[Union[str, Anchor]] = None
    rotation: int = 0
    mirror: bool = False

    class Config:
        extra = Extra.forbid


class RouteModel(BaseModel):
    links: Dict[str, str]
    settings: Optional[Dict[str, Any]] = None
    routing_strategy: Optional[str] = None

    class Config:
        extra = Extra.forbid


class NetlistModel(BaseModel):
    """Netlist defined component.

    Attributes:
        instances: dict of instances (name, settings, component).
        placements: dict of placements.
        connections: dict of connections.
        routes: dict of routes.
        name: component name.
        info: information (polarization, wavelength ...).
        settings: input variables.
        pdk: pdk module name.
        ports: exposed component ports.
    """

    instances: Dict[str, ComponentModel]
    placements: Optional[Dict[str, PlacementModel]] = None
    connections: Optional[List[Dict[str, str]]] = None
    routes: Optional[Dict[str, RouteModel]] = None
    name: Optional[str] = None
    info: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    pdk: Optional[str] = None
    ports: Optional[Dict[str, str]] = None

    class Config:
        extra = Extra.forbid

    # factory: Dict[str, ComponentFactory] = {}
    # def add_instance(self, name: str, component: str, **settings) -> None:
    #     assert component in self.factory.keys()
    #     component_model = ComponentModel(component=component, settings=settings)
    #     self.instances[name] = component_model

    # def add_route(self, port1: Port, port2: Port, **settings) -> None:
    #     self.routes = component_model


RouteFactory = Callable[..., Route]


class TypedArray(np.ndarray):
    """based on https://github.com/samuelcolvin/pydantic/issues/380"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        return np.array(val, dtype=cls.inner_type)


class ArrayMeta(type):
    def __getitem__(self, t):
        return type("Array", (TypedArray,), {"inner_type": t})


class Array(np.ndarray, metaclass=ArrayMeta):
    pass


__all__ = (
    "ComponentFactory",
    "ComponentFactoryDict",
    "ComponentSpec",
    "ComponentOrPath",
    "ComponentOrReference",
    "Coordinate",
    "Coordinates",
    "CrossSectionFactory",
    "CrossSectionOrFactory",
    "MultiCrossSectionAngleSpec",
    "Float2",
    "Float3",
    "Floats",
    "Int2",
    "Int3",
    "Ints",
    "Layer",
    "Layers",
    "NameToFunctionDict",
    "Number",
    "PathType",
    "PathTypes",
    "Route",
    "RouteFactory",
    "Routes",
    "Strs",
)


def write_schema(model: BaseModel = NetlistModel) -> None:
    s = model.schema_json()
    d = OmegaConf.create(s)

    dirpath = pathlib.Path(__file__).parent / "schemas"

    f1 = dirpath / "netlist.yaml"
    f1.write_text(OmegaConf.to_yaml(d))

    f2 = dirpath / "netlist.json"
    f2.write_text(json.dumps(OmegaConf.to_container(d)))


if __name__ == "__main__":
    write_schema()

    import jsonschema
    import yaml

    from gdsfactory.config import CONFIG

    schema_path = CONFIG["schema_netlist"]
    schema_dict = json.loads(schema_path.read_text())

    yaml_text = """

name: mzi

pdk: ubcpdk

settings:
   dy: -90

info:
    polarization: te
    wavelength: 1.55
    description: mzi for ubcpdk

instances:
    yr:
      component: y_splitter
    yl:
      component: y_splitter

placements:
    yr:
        rotation: 180
        x: 100
        y: 0

routes:
    route_top:
        links:
            yl,opt2: yr,opt3
        settings:
            cross_section: strip
    route_bot:
        links:
            yl,opt3: yr,opt2
        routing_strategy: get_bundle_from_steps
        settings:
          steps: [dx: 30, dy: '${settings.dy}', dx: 20]
          cross_section: strip

ports:
    o1: yl,opt1
    o2: yr,opt1
"""

    yaml_dict = yaml.safe_load(yaml_text)
    jsonschema.validate(yaml_dict, schema_dict)

    # from gdsfactory.components import factory
    # c = NetlistModel(factory=factory)
    # c.add_instance("mmi1", "mmi1x2", length=13.3)
