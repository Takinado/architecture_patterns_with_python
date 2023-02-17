from dataclasses import dataclass
from datetime import date

# from typing import NewType
#
# Quantity = NewType("Quantity", int)
# Sku = NewType("Sku", str)
# Reference = NewType("Reference", str)


class OutOfStock(Exception):
    pass


# @dataclass(frozen=True)
@dataclass(unsafe_hash=True)
class OrderLine:  # Товарная позиция заказа
    order_id: str
    sku: str  # единица складского учета (stock-keeping unit, SKU)
    quantity: int


class Batch:  # Партия
    def __init__(
        self, reference: str, sku: str, quantity: int, eta: date | None
    ) -> None:
        self.reference = reference
        self.sku = sku  # единица складского учета (stock-keeping unit, SKU)
        self.eta = eta  # предполагаемый срок прибытия (estimated arrival time, ETA)
        self._purchased_quantity: int = quantity
        self._allocations: set[OrderLine] = set()

    def __repr__(self):
        return f"<Партия {self.reference}>"

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        return hash(self.reference)

    # def __gt__(self, other):
    #     if self.eta is None:
    #         return False
    #     if other.eta is None:
    #         return True
    #     return self.eta > other.eta

    def __lt__(self, other):
        if self.eta is None:
            return True
        if other.eta is None:
            return False
        return self.eta < other.eta

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine) -> None:
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def allocated_quantity(self) -> int:
        return sum(line.quantity for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.quantity


def allocate(line: OrderLine, batches: list[Batch]) -> str:
    """
    Операция службы предметной области.
    """
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f"Артикула {line.sku} нет в достаточном количестве.")
