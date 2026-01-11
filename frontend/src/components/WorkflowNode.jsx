import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import {
  Play,
  MessageSquare,
  GitBranch,
  FormInput,
  Wrench,
  CircleStop
} from 'lucide-react';

const nodeIcons = {
  start: Play,
  llm: MessageSquare,
  condition: GitBranch,
  gather: FormInput,
  tool: Wrench,
  end: CircleStop
};

const nodeColors = {
  start: '#10b981',
  llm: '#6366f1',
  condition: '#f59e0b',
  gather: '#8b5cf6',
  tool: '#3b82f6',
  end: '#ef4444'
};

const nodeLabels = {
  start: 'Start',
  llm: 'LLM',
  condition: 'Condition',
  gather: 'Gather',
  tool: 'Tool',
  end: 'End'
};

const WorkflowNode = memo(({ data, selected }) => {
  const Icon = nodeIcons[data.nodeType] || MessageSquare;
  const color = nodeColors[data.nodeType] || '#6366f1';
  const label = nodeLabels[data.nodeType] || 'Node';

  const showSourceHandle = data.nodeType !== 'end';
  const showTargetHandle = data.nodeType !== 'start';

  return (
    <div className={`workflow-node ${selected ? 'selected' : ''}`}>
      {showTargetHandle && (
        <Handle
          type="target"
          position={Position.Top}
          style={{ background: color }}
        />
      )}
      
      <div 
        className="workflow-node-header"
        style={{ '--node-color': color }}
      >
        <div className="workflow-node-icon">
          <Icon />
        </div>
        <div className="workflow-node-title">
          <h4>{data.label || label}</h4>
          <span>{label}</span>
        </div>
      </div>

      <div className="workflow-node-body">
        {data.nodeType === 'llm' && (
          <div className="workflow-node-field">
            <label>System Prompt</label>
            <textarea
              value={data.config?.customPrompt || ''}
              placeholder="Enter system prompt..."
              readOnly
            />
          </div>
        )}

        {data.nodeType === 'gather' && (
          <div className="workflow-node-field">
            <label>Field Name</label>
            <input
              type="text"
              value={data.config?.fieldName || ''}
              placeholder="e.g., customer_email"
              readOnly
            />
          </div>
        )}

        {data.nodeType === 'condition' && (
          <div className="workflow-node-field">
            <label>Condition</label>
            <input
              type="text"
              value={data.config?.condition || ''}
              placeholder="e.g., intent == sales"
              readOnly
            />
          </div>
        )}

        {data.nodeType === 'tool' && (
          <div className="workflow-node-field">
            <label>Tool</label>
            <input
              type="text"
              value={data.config?.toolId || ''}
              placeholder="Select a tool..."
              readOnly
            />
          </div>
        )}

        {data.tools && data.tools.length > 0 && (
          <div className="workflow-node-field">
            <label>Available Tools</label>
            <div className="tool-chips">
              {data.tools.map((tool) => (
                <span key={tool} className="tool-chip active">
                  {tool}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {showSourceHandle && (
        <Handle
          type="source"
          position={Position.Bottom}
          style={{ background: color }}
        />
      )}
    </div>
  );
});

WorkflowNode.displayName = 'WorkflowNode';

export default WorkflowNode;
