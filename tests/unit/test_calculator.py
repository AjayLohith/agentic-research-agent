import pytest
from app.tools.calculator import SafeCalculator, CalculatorInput


@pytest.fixture
def calculator():
    return SafeCalculator()


@pytest.mark.asyncio
async def test_calculator_basic_arithmetic(calculator):
    res = await calculator.run(expression="10 + 5 * 2")
    assert res.success is True
    assert res.data["result"] == 20.0
    assert res.data["expression"] == "10 + 5 * 2"


@pytest.mark.asyncio
async def test_calculator_percentage_and_division(calculator):
    res = await calculator.run(expression="125 / 500 * 100")
    assert res.success is True
    assert res.data["result"] == 25.0


@pytest.mark.asyncio
async def test_calculator_parentheses_and_modulo(calculator):
    res = await calculator.run(expression="(50 + 10) % 7")
    assert res.success is True
    assert res.data["result"] == 4.0


@pytest.mark.asyncio
async def test_calculator_division_by_zero(calculator):
    res = await calculator.run(expression="100 / 0")
    assert res.success is False
    assert "Division by zero" in res.error


@pytest.mark.asyncio
async def test_calculator_empty_expression(calculator):
    res = await calculator.run(expression="   ")
    assert res.success is False
    assert "Empty" in res.error


@pytest.mark.asyncio
async def test_calculator_syntax_error(calculator):
    res = await calculator.run(expression="10 + * 5")
    assert res.success is False
    assert "syntax" in res.error.lower()


@pytest.mark.asyncio
async def test_calculator_security_sandbox_blocks_arbitrary_code(calculator):
    # Attempt import
    res1 = await calculator.run(expression="__import__('os').system('dir')")
    assert res1.success is False

    # Attempt built-in exec
    res2 = await calculator.run(expression="exec('x = 1')")
    assert res2.success is False

    # Attempt variable access
    res3 = await calculator.run(expression="open('/etc/passwd')")
    assert res3.success is False
