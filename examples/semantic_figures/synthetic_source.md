# Synthetic figure input for executable examples

These descriptions are invented test fixtures, not experiments or a published
network. They contain no measured attention weights, adjacency values or signals.

## Graph attention

A 12 × 32 input feature tensor passes to an attention operator with three heads
and then to a 12 × 16 output feature tensor. The head fusion operation and the
actual graph adjacency are not supplied. Only the neighborhood operation is
illustrated symbolically. The three named stages are connected in that order.

## Residual branch

An N × 16 tensor enters a temporal convolution and then an N × 16 main-branch
feature state. An unchanged shortcut from the input joins that main-branch state
at an addition operator, yielding an N × 16 output. No convolution kernel size,
weights or measured traces are supplied. The convolution window is schematic.

The examples test semantic compilation and source boundaries. They are not a
held-out paper benchmark, independent scientific review, or journal-size proof.
