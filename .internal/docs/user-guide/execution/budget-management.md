# Managing Execution Budget

Enrolled users can run quantum programs on multiple backends without needing to provide their own credentials, by using `run_through_classiq`.

When a job is submitted using `run_through_classiq`, it will only proceed if the estimated cost is within the remaining budget allocated for the chosen provider.

Additionally, we offer methods to monitor usage and set limits, helping you control and optimize your spending.

For example, to set up execution using `run_through_classiq` on the Amazon Braket SV1 simulator:

[comment]: DO_NOT_TEST

```python
from classiq import *


@qfunc
def main(x: Output[QBit]):
    allocate(x)


qprog = synthesize(main)

exec_pref = ExecutionPreferences(
    backend_preferences=AwsBackendPreferences(
        backend_name="SV1",
        run_through_classiq=True,
    )
)

# Assuming you have a pre-defined quantum program "qprog"

with ExecutionSession(qprog, execution_preferences=exec_pref) as es:
    result = es.sample()
```

## Checking the Remaining Budget

To view your remaining execution budget, run the following command:

[comment]: DO_NOT_TEST

```python
from classiq import *

budget = get_budget()
print(budget)
```

A table will be displayed:

![Budget](../resources/budget.png)

## Setting a Custom Budget Limit

You can also define a custom spending limit to stay within a desired budget (lower than your total budget). For example:

[comment]: DO_NOT_TEST

```python
from classiq import *

budget = set_budget_limit(
    provider=ProviderVendor.AMAZON_BRAKET,
    limit=90,  # Set a custom limit below the provider's remaining budget
)
```

To verify the updated limit, simply run `print(budget)` again. The output will now reflect the new budget cap:

![Budget_limited](../resources/budget_with_limit.png)

To clear user-defined budget limits, run `clear_budget_limit("Amazon Braket")`.
