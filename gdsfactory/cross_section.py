"""You can define a path with a list of points

To create a component you need to extrude the path with a cross-section.

Based on phidl.device_layout.CrossSection
"""
from functools import partial
from typing import Iterable, Optional, Tuple, Union

import pydantic
from phidl.device_layout import CrossSection

from gdsfactory.tech import TECH, Section

LAYER = TECH.layer
Layer = Tuple[int, int]
PortName = Union[str, int]


@pydantic.validate_arguments
def cross_section(
    width: float = 0.5,
    layer: Tuple[int, int] = (1, 0),
    width_wide: Optional[float] = None,
    auto_widen: bool = True,
    auto_widen_minimum_length: float = 200.0,
    taper_length: float = 10.0,
    radius: float = 10.0,
    cladding_offset: float = 3.0,
    layer_cladding: Optional[Layer] = None,
    layers_cladding: Optional[Tuple[Layer, ...]] = None,
    sections: Optional[Tuple[Section, ...]] = None,
    port_names: Tuple[PortName, PortName] = (1, 2),
    min_length: float = 10e-3,
    start_straight: float = 10e-3,
    end_straight_offset: float = 10e-3,
    snap_to_grid: Optional[float] = None,
) -> CrossSection:
    """Returns CrossSection from TECH.waveguide settings.

    Args:
        width: main of the waveguide
        layer: main layer
        width_wide: taper to widen waveguides for lower loss
        auto_widen: taper to widen waveguides for lower loss
        auto_widen_minimum_length: minimum straight length for auto_widen
        taper_length: taper_length for auto_widen
        radius: bend radius
        cladding_offset: offset for layers_cladding
        layer_cladding:
        layers_cladding:
        sections: Sections(width, offset, layer, ports)
        port_names: for input and output (1, 2),
        min_length: 10e-3 for routing
        start_straight: for routing
        end_straight_offset: for routing
        snap_to_grid: can snap points to grid when extruding the path
    """

    x = CrossSection()
    x.add(width=width, offset=0, layer=layer, ports=port_names)

    sections = sections or []
    for section in sections:
        if isinstance(section, dict):
            x.add(
                width=section["width"],
                offset=section["offset"],
                layer=section["layer"],
                ports=section["ports"],
            )
        else:
            x.add(
                width=section.width,
                offset=section.offset,
                layer=section.layer,
                ports=section.ports,
            )

    x.info = dict(
        width=width,
        layer=layer,
        width_wide=width_wide,
        auto_widen=auto_widen,
        auto_widen_minimum_length=auto_widen_minimum_length,
        taper_length=taper_length,
        radius=radius,
        cladding_offset=cladding_offset,
        layer_cladding=layer_cladding,
        layers_cladding=layers_cladding,
        sections=sections,
        min_length=min_length,
        start_straight=start_straight,
        end_straight_offset=end_straight_offset,
        snap_to_grid=snap_to_grid,
    )
    return x


def pin(
    width: float = 0.5,
    layer: Tuple[int, int] = LAYER.WG,
    layer_slab: Tuple[int, int] = LAYER.SLAB90,
    width_i: float = 0.0,
    width_p: float = 1.0,
    width_n: float = 1.0,
    width_pp: float = 1.0,
    width_np: float = 1.0,
    width_ppp: float = 1.0,
    width_npp: float = 1.0,
    layer_p: Tuple[int, int] = LAYER.P,
    layer_n: Tuple[int, int] = LAYER.N,
    layer_pp: Tuple[int, int] = LAYER.Pp,
    layer_np: Tuple[int, int] = LAYER.Np,
    layer_ppp: Tuple[int, int] = LAYER.Ppp,
    layer_npp: Tuple[int, int] = LAYER.Npp,
    cladding_offset: float = 0,
    layers_cladding: Optional[Iterable[Tuple[int, int]]] = None,
) -> CrossSection:
    """PIN doped cross_section.

    .. code::

                                   layer
                           |<------width------>|
                            ____________________
                           |     |       |     |
        ___________________|     |       |     |__________________________|
                                 |       |                                |
            P++     P+     P     |   I   |     N        N+         N++    |
        __________________________________________________________________|
                                                                          |
                                 |width_i| width_n | width_np | width_npp |
                                    0    oi        on        onp         onpp

    """
    x = CrossSection()
    x.add(width=width, offset=0, layer=layer, ports=["in", "out"])

    oi = width_i / 2
    on = oi + width_n
    onp = oi + width_n + width_np
    onpp = oi + width_n + width_np + width_npp

    op = -oi - width_p
    opp = op - width_pp
    oppp = opp - width_ppp

    offset_n = (oi + on) / 2
    offset_np = (on + onp) / 2
    offset_npp = (onp + onpp) / 2

    offset_p = (-oi + op) / 2
    offset_pp = (op + opp) / 2
    offset_ppp = (opp + oppp) / 2

    width_slab = abs(onpp) + abs(oppp)
    x.add(width=width_slab, offset=0, layer=layer_slab)

    x.add(width=width_n, offset=offset_n, layer=layer_n)
    x.add(width=width_np, offset=offset_np, layer=layer_np)
    x.add(width=width_npp, offset=offset_npp, layer=layer_npp)

    x.add(width=width_p, offset=offset_p, layer=layer_p)
    x.add(width=width_pp, offset=offset_pp, layer=layer_pp)
    x.add(width=width_ppp, offset=offset_ppp, layer=layer_ppp)

    for layer_cladding in layers_cladding or []:
        x.add(width=width_slab + 2 * cladding_offset, offset=0, layer=layer_cladding)

    s = dict(
        width=width,
        layer=layer,
        cladding_offset=cladding_offset,
        layers_cladding=layers_cladding,
    )
    x.info = s
    return x


@pydantic.validate_arguments
def strip_heater_metal_undercut(
    wg_width: float = 0.5,
    heater_width: float = 1.0,
    trench_width: float = 6.5,
    trench_gap: float = 2.0,
    layer_waveguide: Layer = LAYER.WG,
    layer_heater: Layer = LAYER.HEATER,
    layer_trench: Layer = LAYER.DEEPTRENCH,
    **kwargs,
):
    """Returns strip cross_section with top metal and undercut trenches on both sides.
    dimensions from https://doi.org/10.1364/OE.18.020298

    Args:
        wg_width:
        heater_width:
        trench_width:
        trench_gap: from waveguide edge to trench edge
        layer_waveguide:
        layer_heater:
        layer_trench:
        **kwargs: for cross_section

    """
    trench_offset = trench_gap + trench_width / 2 + wg_width / 2
    return cross_section(
        width=wg_width,
        layer=layer_waveguide,
        sections=(
            Section(layer=layer_heater, width=heater_width),
            Section(layer=layer_trench, width=trench_width, offset=+trench_offset),
            Section(layer=layer_trench, width=trench_width, offset=-trench_offset),
        ),
        **kwargs,
    )


@pydantic.validate_arguments
def strip_heater_metal(
    wg_width: float = 0.5,
    heater_width: float = 1.0,
    layer_waveguide: Layer = LAYER.WG,
    layer_heater: Layer = LAYER.HEATER,
    **kwargs,
):
    """Returns strip cross_section with top heater metal.
    dimensions from https://doi.org/10.1364/OE.18.020298
    """
    return cross_section(
        width=wg_width,
        layer=layer_waveguide,
        sections=(Section(layer=layer_heater, width=heater_width),),
        **kwargs,
    )


@pydantic.validate_arguments
def rib_heater_doped(
    wg_width: float = 0.5,
    heater_width: float = 1.0,
    heater_gap: float = 0.8,
    layer_waveguide: Layer = LAYER.WG,
    layer_heater: Layer = LAYER.Npp,
    layer_slab: Layer = LAYER.SLAB90,
    **kwargs,
):
    """Returns rib cross_section with N++ doped heaters on both sides.
    dimensions from https://doi.org/10.1364/OE.27.010456
    """
    slab_width = wg_width + 2 * heater_gap + 2 * heater_width
    heater_offset = wg_width / 2 + heater_gap + heater_width / 2
    return cross_section(
        width=wg_width,
        layer=layer_waveguide,
        sections=(
            Section(
                layer=layer_heater,
                width=heater_width,
                offset=+heater_offset,
            ),
            Section(
                layer=layer_heater,
                width=heater_width,
                offset=-heater_offset,
            ),
            Section(width=slab_width, layer=layer_slab, name="slab"),
        ),
        **kwargs,
    )


strip = partial(cross_section)
rib = partial(
    cross_section, sections=(Section(width=6, layer=LAYER.SLAB90, name="slab90"),)
)
metal1 = partial(cross_section, layer=LAYER.M1, width=10.0)
metal2 = partial(cross_section, layer=LAYER.M2, width=10.0)
metal3 = partial(cross_section, layer=LAYER.M3, width=10.0)
nitride = partial(cross_section, layer=LAYER.WGN, width=1.0)


cross_section_factory = dict(
    cross_section=cross_section,
    strip=strip,
    rib=rib,
    nitride=nitride,
    metal1=metal1,
    metal2=metal2,
    metal3=metal3,
    pin=pin,
    strip_heater_metal_undercut=strip_heater_metal_undercut,
    strip_heater_metal=strip_heater_metal,
    rib_heater_doped=rib_heater_doped,
)

if __name__ == "__main__":
    import gdsfactory as gf

    P = gf.path.straight()
    # P = gf.path.euler(radius=10, use_eff=True)
    # P = euler()
    # P = gf.Path()
    # P.append(gf.path.straight(length=5))
    # P.append(gf.path.arc(radius=10, angle=90))
    # P.append(gf.path.spiral())

    # Create a blank CrossSection
    # X = CrossSection()
    # X.add(width=2.0, offset=-4, layer=LAYER.HEATER, ports=["HW1", "HE1"])
    # X.add(width=0.5, offset=0, layer=LAYER.SLAB90, ports=["in", "out"])
    # X.add(width=2.0, offset=4, layer=LAYER.HEATER, ports=["HW0", "HE0"])

    # Combine the Path and the CrossSection into a Component
    # X = pin(width=0.5, width_i=0.5)
    # x = strip(width=0.5)

    # X = cross_section(width=3, layer=(2, 0))
    # X = cross_section(**s)
    # X = strip_heater_metal_undercut()
    # X = rib_heater_doped()

    X = strip_heater_metal_undercut()
    c = gf.path.extrude(P, X)

    # c = gf.path.component(P, strip(width=2, layer=LAYER.WG, cladding_offset=3))
    # c = gf.add_pins(c)
    # c << gf.components.bend_euler(radius=10)
    # c << gf.components.bend_circular(radius=10)
    c.show()
