---
search:
    boost: 2.872
---

# Getting Started with Quantum Program Synthesis

The first steps in quantum program synthesis are defining the algorithms, its constraints,
and your preferences. These are described in detail in the following sections.

Once your model is fully defined, it is time to synthesize it.

=== "IDE"

    In the IDE, describe the model in the [model](https://platform.classiq.io/dsl-synthesis) page.
    After writing down the model, click `Synthesize` on the bottom right of the page.
    After synthesis, you are automatically redirected to the quantum program page.

=== "SDK"

    Initiate the synthesis process by performing the `synthesize` method on a model. Alternatively, you can use the async
    `synthesize_async` method as part of an async code.

    ```python
    from classiq import qfunc, Output, QBit, allocate, synthesize


    @qfunc
    def main(res: Output[QBit]) -> None:
        allocate(1, res)


    qprog = synthesize(main)
    ```
