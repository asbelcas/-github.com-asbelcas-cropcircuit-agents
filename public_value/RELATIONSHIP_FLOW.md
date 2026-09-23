# Relationship Flow View v0.1

CropCircuit now has a small, inspectable relationship graph for showing **how parts of a farm are connected**, where stress or uncertainty sits, and what evidence supports each recorded connection.

This is not a causal-discovery engine.

## Why this exists

A farm problem rarely belongs to only one object.

A behavior issue can involve:

- animals
- pasture
- water
- fencing
- labor
- weather
- money
- information

The relationship view makes those recorded connections visible without pretending the graph is the territory.

## Nodes

A node is a locally meaningful participant, resource, place, process, or constraint.

Examples:

- flock
- paddock
- water line
- milking group
- worker shift
- feed inventory
- cash reserve
- customer channel

A node can be marked:

- healthy
- watch
- stressed
- unknown

Evidence references and unknowns remain attached.

## Edges

An edge records a relationship or flow between two nodes.

Each edge includes:

- from
- to
- plain-language relationship
- flow kind
- state
- evidence references
- unknowns
- note

Supported flow kinds include:

- water
- nutrients
- animals
- materials
- labor
- money
- information
- trust
- energy
- risk
- other

## Stress and slack

v0.1 does not calculate a universal "farm health score."

Instead it surfaces:

- stressed nodes
- unknown nodes
- stressed edges
- unknown edges
- edges carrying unresolved unknowns
- isolated nodes

The operator decides what those facts mean in context.

## Local traces

`traceRelationships()` returns the recorded neighborhood around one node to a chosen depth.

This is useful for questions like:

> What other recorded parts of the farm touch paddock 4?

It deliberately says **recorded relationships**, not causal effects.

## Evidence discipline

A non-unknown node or edge without evidence references receives a warning.

This does not forbid farmer knowledge. A farmer observation can itself be a valid evidence reference.

The purpose is to stop model-generated edges from silently hardening into "facts."

## Files

- [relationship_flow.js](relationship_flow.js)
- [relationship_flow.test.mjs](relationship_flow.test.mjs)

## Design principle

**Show the relationships we have evidence for. Show the unknowns we do not. Do not draw causation just because two things are connected.**
