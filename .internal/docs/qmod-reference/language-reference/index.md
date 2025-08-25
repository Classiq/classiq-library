---
search:
    boost: 3.358
---

# Qmod Language Reference

The Qmod reference manual describes the language concepts and constructs, and demonstrates
them through examples. The examples are present in both input formats - the Qmod native
syntax and its Python embedding.

## Qmod Native Syntax Rules

Qmod generally follows the C language lexical and syntactic conventions.
Identifiers, literal values, and inline comments, are styled after the C family, as well
as syntactic nesting and statement terminators.

## Python Embedding Design

The embedding of Qmod in Python leverages Python mechanisms for language enhancements,
such as type-hints, decorators, and "magic methods". The regular
Python execution of decorated functions and the statements under them constructs a
representation of the Qmod description. Expressions are generally evaluated symbolically,
that is, construct a representation of the expression that retains the symbols whose
values are unknown at that point.
