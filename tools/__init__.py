import tqdm
import torch

import torch.nn.functional as F

from torch.utils.data import TensorDataset, DataLoader


def dataset_from_numpy(*ndarrays, dtype=None, device=None):
    """Creates :class:`TensorDataset` from the passed :class:`numpy.ndarray`-s.

    Each returned tensor in the TensorDataset and :attr:`ndarray` share
    the same memory, unless a type cast or device transfer took place.
    Modifications to any tensor in the dataset will be reflected in respective
    :attr:`ndarray` and vice versa.

    Each returned tensor in the dataset is not resizable.

    See Also
    --------
    torch.from_numpy : create a tensor from an ndarray.
    """
    tensors = map(torch.from_numpy, ndarrays)

    return TensorDataset(*[t.to(device, dtype) for t in tensors])


def fit(model, dataset, batch_size=32, n_epochs=1,
        loss_fn=F.nll_loss, verbose=False):
    """Fit the model with SGD on the specified dataset."""
    # get the model's device
    device = next(model.parameters()).device

    # an optimizer for model's parameters
    optim = torch.optim.Adam(model.parameters(), lr=1e-3)  # , weight_decay=1e-5)

    # stochastic minibatch generator for the training loop
    feed = DataLoader(dataset, shuffle=True,
                                       batch_size=batch_size)
    for epoch in tqdm.tqdm(range(n_epochs), disable=not verbose):

        model.train()
        for X, y in feed:
            # forward pass
            output = model(X.to(device))

            # criterion: batch-average loss
            loss = loss_fn(output, y.to(device), reduction="mean")

            # get gradients with backward pass
            optim.zero_grad()
            loss.backward()

            # SGD update
            optim.step()

    return model


def apply(model, dataset):
    """Collect model's outputs on the dataset without autograd."""
    model.eval()

    # get the model's device
    device = next(model.parameters()).device

    # batch generator for the evaluation loop
    feed = DataLoader(dataset, batch_size=512, shuffle=False)

    # disable gradients (huge speed up!)
    with torch.no_grad():

        # compute and collect the outputs
        return torch.cat([
            model(X.to(device)).cpu() for X, *rest in feed
        ], dim=0)