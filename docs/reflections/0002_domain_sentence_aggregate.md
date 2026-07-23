# Reflection: Aggregate Immutability

**Feature Branch:** `feat/domain-sentence-aggregate`

## Context

The purpose of this branch was to introduce the first Aggregate Root in the Text Analysis bounded context.

The `Sentence` model represents an ordered collection of `Token` value objects and is responsible for protecting the invariants of that collection.

## Initial Approach

After implementing the initial tests, the first implementation used a standard Python `list` to store the collection of tokens.

This was a natural choice because lists are the default collection type used frequently in Python.

However, although the `Sentence` dataclass was marked as frozen, the internal list remained mutable.

Example:

```python
sentence.tokens.append(Token("世界"))
```

would still modify the state of the aggregate.

## Testing Discovery

The initial immutability test only verified that the attribute itself could not be reassigned:

```python
sentence.tokens = []
```

This passed because `frozen=True` prevents attribute assignment.

However, this did not verify that the contents of the aggregate were protected.

This highlighted that immutability has multiple levels:

1. The aggregate reference cannot be replaced.
2. The aggregate does not retain references to externally owned mutable objects.
3. The aggregate does not expose mutable internal state.

## Revised Design

The internal representation was changed from:

```python
list[Token]
```

to:

```python
tuple[Token, ...]
```

The constructor accepts a sequence of tokens but creates an immutable internal representation.

This ensures that:

- changes to the original input collection do not affect the aggregate;
- consumers cannot mutate the aggregate through the public API;
- the aggregate maintains ownership of its internal state.

## Lessons Learned

Making an object immutable requires considering the mutability of all objects it contains.

A frozen dataclass provides protection against changing attributes, but it does not automatically make nested mutable objects immutable.

When designing future domain aggregates, collection choices should be guided by the required invariants rather than convenience.

Before choosing a data structure, consider:

- Who owns this data?
- Can external code modify it?
- Does mutation violate a business rule?
- Should the aggregate expose this state at all?

## Architectural Impact

This reinforced the Aggregate Root principle from Domain-Driven Design:

> An aggregate is responsible for maintaining its own invariants.

Future domain aggregates should follow the same pattern of protecting internal state and exposing behaviour rather than mutable data structures.
