/**
 * CropCircuit Relationship Flow View v0.1
 *
 * Inspectable graph of farm participants, resources, flows, dependencies,
 * stress, evidence, and unknowns. It does not infer causation from proximity.
 */

const NODE_STATES = new Set(["healthy", "watch", "stressed", "unknown"]);
const EDGE_STATES = new Set(["healthy", "watch", "stressed", "unknown"]);
const FLOW_KINDS = new Set([
  "water",
  "nutrients",
  "animals",
  "materials",
  "labor",
  "money",
  "information",
  "trust",
  "energy",
  "risk",
  "other",
]);

function isText(value) {
  return typeof value === "string" && value.trim().length > 0;
}
function array(value) {
  return Array.isArray(value) ? value : [];
}
function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

export function validateRelationshipMap(map = {}) {
  const errors = [];
  const warnings = [];

  if (map.schema_version !== "0.1") errors.push("schema_version must equal 0.1");
  if (!isText(map.map_id)) errors.push("map_id is required");
  if (!isText(map.updated_at)) errors.push("updated_at is required");

  const nodes = array(map.nodes);
  const edges = array(map.edges);
  const nodeIds = new Set();

  nodes.forEach((node, index) => {
    if (!isText(node?.id)) errors.push(`nodes[${index}].id is required`);
    if (!isText(node?.label)) errors.push(`nodes[${index}].label is required`);
    if (!NODE_STATES.has(node?.state)) errors.push(`nodes[${index}].state is not recognized`);
    if (isText(node?.id)) {
      if (nodeIds.has(node.id)) errors.push(`duplicate node id: ${node.id}`);
      nodeIds.add(node.id);
    }
    if (!array(node?.evidence_refs).length && node?.state !== "unknown") {
      warnings.push(`nodes[${index}] has a non-unknown state without evidence_refs`);
    }
  });

  const edgeIds = new Set();
  edges.forEach((edge, index) => {
    if (!isText(edge?.id)) errors.push(`edges[${index}].id is required`);
    if (isText(edge?.id)) {
      if (edgeIds.has(edge.id)) errors.push(`duplicate edge id: ${edge.id}`);
      edgeIds.add(edge.id);
    }
    if (!isText(edge?.from)) errors.push(`edges[${index}].from is required`);
    if (!isText(edge?.to)) errors.push(`edges[${index}].to is required`);
    if (isText(edge?.from) && !nodeIds.has(edge.from)) {
      errors.push(`edges[${index}].from references unknown node: ${edge.from}`);
    }
    if (isText(edge?.to) && !nodeIds.has(edge.to)) {
      errors.push(`edges[${index}].to references unknown node: ${edge.to}`);
    }
    if (!isText(edge?.relationship)) {
      errors.push(`edges[${index}].relationship is required`);
    }
    if (!FLOW_KINDS.has(edge?.flow_kind)) {
      errors.push(`edges[${index}].flow_kind is not recognized`);
    }
    if (!EDGE_STATES.has(edge?.state)) {
      errors.push(`edges[${index}].state is not recognized`);
    }
    if (!array(edge?.evidence_refs).length && edge?.state !== "unknown") {
      warnings.push(`edges[${index}] has a non-unknown state without evidence_refs`);
    }
    if (edge?.from === edge?.to) {
      warnings.push(`edges[${index}] is a self-relationship`);
    }
  });

  return { valid: errors.length === 0, errors, warnings };
}

export function summarizeRelationshipMap(map = {}) {
  const validation = validateRelationshipMap(map);
  if (!validation.valid) {
    return {
      valid: false,
      validation,
      counts: {},
      focus: [],
      isolated_nodes: [],
    };
  }

  const nodes = clone(map.nodes);
  const edges = clone(map.edges);
  const degree = new Map(nodes.map(node => [node.id, 0]));

  edges.forEach(edge => {
    degree.set(edge.from, (degree.get(edge.from) || 0) + 1);
    degree.set(edge.to, (degree.get(edge.to) || 0) + 1);
  });

  const isolatedNodes = nodes
    .filter(node => (degree.get(node.id) || 0) === 0)
    .map(node => node.id);

  const focus = [
    ...nodes
      .filter(node => ["stressed", "unknown"].includes(node.state))
      .map(node => ({
        kind: "node",
        id: node.id,
        state: node.state,
        label: node.label,
        evidence_refs: array(node.evidence_refs),
        unknowns: array(node.unknowns),
      })),
    ...edges
      .filter(edge => ["stressed", "unknown"].includes(edge.state) || array(edge.unknowns).length)
      .map(edge => ({
        kind: "edge",
        id: edge.id,
        state: edge.state,
        label: `${edge.from} -> ${edge.to}: ${edge.relationship}`,
        flow_kind: edge.flow_kind,
        evidence_refs: array(edge.evidence_refs),
        unknowns: array(edge.unknowns),
      })),
  ];

  return {
    valid: true,
    validation,
    counts: {
      nodes: nodes.length,
      edges: edges.length,
      stressed_nodes: nodes.filter(x => x.state === "stressed").length,
      unknown_nodes: nodes.filter(x => x.state === "unknown").length,
      stressed_edges: edges.filter(x => x.state === "stressed").length,
      unknown_edges: edges.filter(x => x.state === "unknown").length,
      edges_with_unknowns: edges.filter(x => array(x.unknowns).length).length,
    },
    focus,
    isolated_nodes: isolatedNodes,
  };
}

export function traceRelationships(map = {}, nodeId, depth = 1) {
  const validation = validateRelationshipMap(map);
  if (!validation.valid) throw new TypeError("A valid relationship map is required");
  if (!map.nodes.some(node => node.id === nodeId)) {
    throw new TypeError("nodeId is not present in the relationship map");
  }

  const maxDepth = Math.max(0, Math.floor(Number(depth) || 0));
  const visitedNodes = new Set([nodeId]);
  const visitedEdges = new Set();
  let frontier = new Set([nodeId]);

  for (let level = 0; level < maxDepth; level++) {
    const next = new Set();
    for (const edge of map.edges) {
      if (!frontier.has(edge.from) && !frontier.has(edge.to)) continue;
      visitedEdges.add(edge.id);
      const otherIds = [edge.from, edge.to];
      for (const id of otherIds) {
        if (!visitedNodes.has(id)) {
          visitedNodes.add(id);
          next.add(id);
        }
      }
    }
    frontier = next;
    if (!frontier.size) break;
  }

  return {
    origin: nodeId,
    depth: maxDepth,
    nodes: map.nodes.filter(node => visitedNodes.has(node.id)).map(clone),
    edges: map.edges.filter(edge => visitedEdges.has(edge.id)).map(clone),
    note: "This trace shows recorded relationships, not proven causal effects.",
  };
}

export { NODE_STATES, EDGE_STATES, FLOW_KINDS };
