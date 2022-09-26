import datetime

from behave import then, when
from hamcrest import assert_that, equal_to, not_

from features.steps.shell import (
    when_i_run_command,
    when_i_run_command_on_machine,
)
from uaclient.defaults import (
    DEFAULT_CONFIG_FILE,
    DEFAULT_PRIVATE_MACHINE_TOKEN_PATH,
)


@when("I update contract to use `{contract_field}` as `{new_value}`")
def when_i_update_contract_field_to_new_value(
    context, contract_field, new_value
):
    if contract_field == "effectiveTo":
        if "days=" in new_value:  # Set timedelta offset from current day
            now = datetime.datetime.utcnow()
            contract_expiry = now + datetime.timedelta(days=int(new_value[5:]))
            new_value = contract_expiry.strftime("%Y-%m-%dT00:00:00Z")
    when_i_run_command(
        context,
        'sed -i \'s/"{}": "[^"]*"/"{}": "{}"/g\' {}'.format(
            contract_field,
            contract_field,
            new_value,
            DEFAULT_PRIVATE_MACHINE_TOKEN_PATH,
        ),
        user_spec="with sudo",
    )


@when("I change contract to staging {user_spec}")
def change_contract_endpoint_to_staging(context, user_spec):
    when_i_run_command(
        context,
        "sed -i 's/contracts.can/contracts.staging.can/' {}".format(
            DEFAULT_CONFIG_FILE
        ),
        user_spec,
    )


def change_contract_endpoint_to_production(context, user_spec):
    when_i_run_command(
        context,
        "sed -i 's/contracts.staging.can/contracts.can/' {}".format(
            DEFAULT_CONFIG_FILE
        ),
        user_spec,
    )


@when("I save the `{key}` value from the contract")
def i_save_the_key_value_from_contract(context, key):
    when_i_run_command(
        context,
        "jq -r '.{}' {}".format(key, DEFAULT_PRIVATE_MACHINE_TOKEN_PATH),
        "with sudo",
    )
    output = context.process.stdout.strip()

    if output:
        if not hasattr(context, "saved_values"):
            setattr(context, "saved_values", {})

        context.saved_values[key] = output


def _get_saved_attr(context, key):
    saved_value = getattr(context, "saved_values", {}).get(key)

    if saved_value is None:
        raise AssertionError(
            "Value for key {} was not previously saved\n".format(key)
        )

    return saved_value


@then(
    "I verify that `{key}` value has been updated on the contract on the `{machine}` machine"  # noqa: E501
)
def i_verify_that_key_value_has_been_updated_on_machine(context, key, machine):
    i_verify_that_key_value_has_been_updated(context, key, machine)


@then("I verify that `{key}` value has been updated on the contract")
def i_verify_that_key_value_has_been_updated(context, key, machine="uaclient"):
    saved_value = _get_saved_attr(context, key)
    when_i_run_command_on_machine(
        context,
        "jq -r '.{}' {}".format(key, DEFAULT_PRIVATE_MACHINE_TOKEN_PATH),
        "with sudo",
        instance_name=machine,
    )
    assert_that(context.process.stdout.strip(), not_(equal_to(saved_value)))


@then("I verify that `{key}` value has not been updated on the contract")
def i_verify_that_key_value_has_not_been_updated(context, key):
    saved_value = _get_saved_attr(context, key)
    when_i_run_command(
        context,
        "jq -r '.{}' {}".format(key, DEFAULT_PRIVATE_MACHINE_TOKEN_PATH),
        "with sudo",
    )
    assert_that(context.process.stdout.strip(), equal_to(saved_value))


@when("I restore the saved `{key}` value on contract")
def i_restore_the_saved_key_value_on_contract(context, key):
    saved_value = _get_saved_attr(context, key)
    when_i_update_contract_field_to_new_value(
        context=context,
        contract_field=key.split(".")[-1],
        new_value=saved_value,
    )