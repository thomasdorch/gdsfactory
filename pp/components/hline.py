from typing import Tuple

from pydantic import validate_arguments

import pp
from pp.cell import cell
from pp.component import Component
from pp.layers import LAYER


@cell
@validate_arguments
def hline(
    length: float = 10.0,
    width: float = 0.5,
    layer: Tuple[int, int] = LAYER.WG,
    port_type: str = "optical",
) -> Component:
    """Horizonal line straight, with ports on east and west sides"""
    c = pp.Component()
    a = width / 2
    if length > 0 and width > 0:
        c.add_polygon([(0, -a), (length, -a), (length, a), (0, a)], layer=layer)

    c.add_port(
        name="W0",
        midpoint=[0, 0],
        width=width,
        orientation=180,
        layer=layer,
        port_type=port_type,
    )
    c.add_port(
        name="E0",
        midpoint=[length, 0],
        width=width,
        orientation=0,
        layer=layer,
        port_type=port_type,
    )

    c.width = width
    c.length = length
    return c


if __name__ == "__main__":
    c = hline(width=10)
    print(c)
    c.show()
