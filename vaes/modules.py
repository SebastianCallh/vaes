from abc import abstractmethod
from math import prod
import torch
from torch import Tensor, nn
from torch import distributions as D


class View(nn.Module):
    def __init__(self, size: torch.Size):
        super().__init__()
        self.size = size

    def forward(self, x: Tensor) -> Tensor:
        return x.view((x.size()[:1] + self.size))


class NNDistribution(nn.Module):
    def __init__(self, name: str, size: torch.Size):
        super().__init__()
        self._size = size
        self._name = name

    @property
    def size(self) -> torch.Size:
        return self._size

    @property
    def name(self) -> str:
        return self._name


class Normal(NNDistribution):
    def __init__(self, in_dim: int, out_size: torch.Size):
        super().__init__("Normal", out_size)
        self.loc = nn.Sequential(
            nn.Linear(in_dim, prod(out_size)),
            View(out_size),
        )
        self.scale = nn.Sequential(
            nn.Linear(in_dim, prod(out_size)),
            View(out_size),
            nn.Softplus(),
        )

    def forward(self, x: Tensor) -> D.Distribution:
        return D.Normal(loc=self.loc(x), scale=self.scale(x))


class Bernoulli(NNDistribution):
    def __init__(self, in_dim: int, out_size: torch.Size):
        super().__init__("Bernoulli", out_size)
        self._size = out_size
        self.f = nn.Sequential(
            nn.Linear(in_dim, prod(out_size)),
            View(out_size),
            nn.Sigmoid(),
        )

    def forward(self, x: Tensor) -> D.Bernoulli:
        # Validate_args=False to allow x in [0, 1]
        return D.Bernoulli(probs=self.f(x), validate_args=False)


class Print(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, x: Tensor) -> Tensor:
        print(x.shape)
        return x


class SimpleCNN(nn.Sequential):
    def __init__(self, num_channels: int, out_dim: int):
        super().__init__(
            nn.Conv2d(num_channels, 20, 5, 1),
            nn.Softplus(),
            nn.BatchNorm2d(20),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(20, 50, 5, 1),
            nn.Softplus(),
            nn.BatchNorm2d(50),
            nn.MaxPool2d(2, 2),
            nn.Flatten(),
            nn.Linear(4 * 4 * 50, 200),
            nn.Softplus(),
            nn.BatchNorm1d(200),
            nn.Dropout(),
            nn.Linear(200, out_dim),
        )


class SimpleTCNN(nn.Sequential):
    def __init__(self, num_channels: int, out_dim: int, h_dim: int = (50, 4, 4)):
        super().__init__(
            nn.Linear(out_dim, prod(h_dim)),
            View(torch.Size(h_dim)),
            nn.Softplus(),
            nn.Upsample(2),
            nn.ConvTranspose2d(50, 20, 5, 1),
            nn.Softplus(),
            nn.BatchNorm2d(20),
            nn.Upsample(2),
            nn.ConvTranspose2d(20, 1, 5, 1),
            nn.Softplus(),
            Print(),
        )