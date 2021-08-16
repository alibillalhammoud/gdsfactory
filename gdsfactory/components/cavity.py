import gdsfactory as gf
from gdsfactory.cell import cell
from gdsfactory.component import Component
from gdsfactory.components.coupler import coupler as coupler_function
from gdsfactory.components.dbr import dbr
from gdsfactory.types import ComponentFactory


@cell
def cavity(
    component: Component = dbr,
    coupler: ComponentFactory = coupler_function,
    length: float = 0.1,
    gap: float = 0.2,
    **coupler_settings
) -> Component:
    r"""Returns  cavity from a coupler and a mirror.

    connects the W0 port of the mirror to E1 and W1 coupler ports
    creating a resonant cavity

    Args:
        component: mirror
        coupler: coupler library
        length: coupler length
        gap: coupler gap
        tech: Technology

    .. code::

      ml (mirror left)              mr (mirror right)
       |                               |
       |W0 - W1__             __E1 - W0|
       |         \           /         |
                  \         /
                ---=========---
             W0    length      E0

    .. plot::
      :include-source:

      import gdsfactory as gf

      c = gf.components.cavity(component=gf.components.dbr())
      c.plot()
    """
    mirror = component() if callable(component) else component
    coupler = (
        coupler(length=length, gap=gap, **coupler_settings)
        if callable(coupler)
        else coupler
    )

    c = gf.Component()
    cr = c << coupler
    ml = c << mirror
    mr = c << mirror

    ml.connect(1, destination=cr.ports[2])
    mr.connect(1, destination=cr.ports["E1"])
    c.add_port(1, port=cr.ports[1])
    c.add_port(2, port=cr.ports[2])
    return c


if __name__ == "__main__":
    from gdsfactory.components.dbr import dbr

    c = cavity(component=dbr())
    c.show()
