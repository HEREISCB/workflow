import { useState, useCallback, useRef } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Play,
  Save,
  Settings,
  Sparkles
} from 'lucide-react';

import WorkflowNode from './components/WorkflowNode';
import NodePalette from './components/NodePalette';
import PropertiesPanel from './components/PropertiesPanel';

const nodeTypes = {
  workflowNode: WorkflowNode
};

const initialNodes = [];
const initialEdges = [];

let nodeId = 0;
const getNodeId = () => `node_${nodeId++}`;

const API_URL = 'http://localhost:8000/api';

function App() {
  const reactFlowWrapper = useRef(null);
  const [nodes, setNodes] = useState(initialNodes);
  const [edges, setEdges] = useState(initialEdges);
  const [selectedNode, setSelectedNode] = useState(null);
  const [workflowName, setWorkflowName] = useState('Untitled Workflow');
  const [workflowId, setWorkflowId] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  const onEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect = useCallback(
    (connection) => setEdges((eds) => addEdge(connection, eds)),
    []
  );

  const onNodeClick = useCallback((_, node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      const position = {
        x: event.clientX - reactFlowWrapper.current.getBoundingClientRect().left - 110,
        y: event.clientY - reactFlowWrapper.current.getBoundingClientRect().top - 25
      };

      const newNode = {
        id: getNodeId(),
        type: 'workflowNode',
        position,
        data: {
          label: type.charAt(0).toUpperCase() + type.slice(1) + ' Node',
          nodeType: type,
          config: {},
          context: {
            includeFields: [],
            includeMessages: false,
            maxMessages: 5
          },
          tools: []
        }
      };

      setNodes((nds) => [...nds, newNode]);
    },
    []
  );

  const updateNodeData = useCallback((nodeId, newData) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId ? { ...node, data: newData } : node
      )
    );
  }, []);

  const saveWorkflow = async () => {
    // Convert nodes/edges to API format
    const workflowNodes = nodes.map((node) => ({
      id: node.id,
      type: node.data.nodeType,
      name: node.data.label,
      position: node.position,
      context: {
        include_fields: node.data.context?.includeFields || [],
        include_messages: node.data.context?.includeMessages || false,
        max_messages: node.data.context?.maxMessages || 5,
        custom_prompt: node.data.config?.customPrompt
      },
      tools: {
        available_tools: node.data.tools || [],
        auto_execute: true,
        max_tool_calls: 3
      },
      config: node.data.config || {},
      next_nodes: edges
        .filter((e) => e.source === node.id)
        .map((e) => e.target)
    }));

    const workflowEdges = edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target
    }));

    try {
      const response = await fetch(`${API_URL}/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: workflowName,
          nodes: workflowNodes,
          edges: workflowEdges
        })
      });

      const data = await response.json();
      setWorkflowId(data.id);
      showToast('Workflow saved successfully!');
    } catch (error) {
      showToast('Failed to save workflow', 'error');
      console.error('Save error:', error);
    }
  };

  const executeWorkflow = async () => {
    if (!workflowId) {
      showToast('Please save the workflow first', 'error');
      return;
    }

    setIsExecuting(true);
    setExecutionResult(null);

    try {
      const response = await fetch(`${API_URL}/workflows/${workflowId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_data: {},
          user_message: 'Hello, I need help with billing.'
        })
      });

      const data = await response.json();
      setExecutionResult(data);
      showToast('Workflow executed!');
    } catch (error) {
      showToast('Execution failed', 'error');
      console.error('Execution error:', error);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <h1>Workflow Builder</h1>
          <p>AI Agent Orchestration</p>
        </div>
        <NodePalette />
      </div>

      {/* Main Canvas */}
      <div className="canvas-container" ref={reactFlowWrapper}>
        <div className="canvas-toolbar">
          <div className="toolbar-left">
            <input
              type="text"
              className="workflow-name"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
            />
          </div>
          <div className="toolbar-right">
            <button className="btn btn-secondary" onClick={saveWorkflow}>
              <Save size={16} />
              Save
            </button>
            <button
              className="btn btn-primary"
              onClick={executeWorkflow}
              disabled={isExecuting}
            >
              {isExecuting ? (
                <>
                  <Sparkles size={16} className="animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play size={16} />
                  Execute
                </>
              )}
            </button>
          </div>
        </div>

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          onDragOver={onDragOver}
          onDrop={onDrop}
          nodeTypes={nodeTypes}
          fitView
          snapToGrid
          snapGrid={[15, 15]}
          defaultEdgeOptions={{
            type: 'smoothstep',
            animated: true
          }}
        >
          <Background variant="dots" gap={20} size={1} />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              const colors = {
                start: '#10b981',
                llm: '#6366f1',
                condition: '#f59e0b',
                gather: '#8b5cf6',
                tool: '#3b82f6',
                end: '#ef4444'
              };
              return colors[node.data?.nodeType] || '#6366f1';
            }}
          />
        </ReactFlow>

        {/* Empty State */}
        {nodes.length === 0 && (
          <div className="empty-state" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
            <div className="empty-state-icon">
              <Settings size={40} />
            </div>
            <h3>Start Building</h3>
            <p>Drag nodes from the left sidebar to create your AI workflow</p>
          </div>
        )}
      </div>

      {/* Properties Panel */}
      {selectedNode && (
        <PropertiesPanel
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
          onUpdate={updateNodeData}
        />
      )}

      {/* Execution Result */}
      {executionResult && (
        <div className="toast success">
          <strong>Output:</strong> {executionResult.output?.substring(0, 100)}...
        </div>
      )}

      {/* Toast Notification */}
      {toast && (
        <div className={`toast ${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}

export default App;
