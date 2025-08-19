---
search:
    boost: 2.972
---

# Supported Modeling

Classiq supports a limited set of modeling configurations. The following tables describe them.

## Variables

<table border="1px solid black">
<tbody>
  <tr>
    <td><b>Index Set</b></td>
    <td  style="text-align:center" colspan="2">List or set</td>
  </tr>
  <tr>
    <td><b>Domain</b></td>
    <td>Binary(equivalent to [0, 1] list) </td>
    <td>Bounded NonNegativeIntegers <br>(equivalent to [0:bound] list)</td>
  </tr>
</tbody>
</table>

## Constraints

<table border="1px solid black">
<tbody>
  <tr>
    <td><b>Constraint type</b></td>
    <td>Equality constraints</td>
    <td>Inequality constraints</td>
  </tr>
  <tr>
    <td><b>Constraint amount</b></td>
    <td style="text-align:center">Multiple, non overlapping</td>
    <td style="text-align:center">Multiple</td>
  </tr>
  <tr>
    <td><b>Expression type</b></td>
    <td colspan="2" style="text-align:center">Linear sum</td>
  </tr>
  <tr>
    <td><b>Variable coefficient</b></td>
    <td colspan="2" style="text-align:center">Positive integer</td>
  </tr>
  <tr>
    <td><b>Constant term</b></td>
    <td colspan="2" style="text-align:center">Positive integer</td>
  </tr>
</tbody>
</table>

## Objective Functions

<table border="1px solid black">
<tbody>
  <tr>
    <td><b>Objective amount</b></td>
    <td colspan="2" style="text-align:center">Single</td>
  </tr>
  <tr>
    <td><b>Variable type</b></td>
    <td style="text-align:center">Binary</td>
    <td style="text-align:center">Integer</td>
  </tr>
  <tr>
    <td><b>Expression type</b></td>
    <td colspan="2" style="text-align:center">Polynomial</td>
  </tr>
  <tr>
    <td><b>Variable coefficient</b></td>
    <td colspan="2" style="text-align:center">Integer or float</td>
  </tr>
</tbody>
</table>
