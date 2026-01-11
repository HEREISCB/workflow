import {
    Play,
    MessageSquare,
    GitBranch,
    FormInput,
    Wrench,
    CircleStop
} from 'lucide-react';

const nodeTypes = [
    {
        type: 'start',
        name: 'Start',
        description: 'Entry point',
        icon: Play,
        color: '#10b981'
    },
    {
        type: 'llm',
        name: 'LLM Agent',
        description: 'AI response with tools',
        icon: MessageSquare,
        color: '#6366f1'
    },
    {
        type: 'condition',
        name: 'Condition',
        description: 'Route based on logic',
        icon: GitBranch,
        color: '#f59e0b'
    },
    {
        type: 'gather',
        name: 'Gather Input',
        description: 'Collect user data',
        icon: FormInput,
        color: '#8b5cf6'
    },
    {
        type: 'tool',
        name: 'Tool',
        description: 'Execute an action',
        icon: Wrench,
        color: '#3b82f6'
    },
    {
        type: 'end',
        name: 'End',
        description: 'Terminate workflow',
        icon: CircleStop,
        color: '#ef4444'
    }
];

const NodePalette = ({ onDragStart }) => {
    const handleDragStart = (event, nodeType) => {
        event.dataTransfer.setData('application/reactflow', nodeType.type);
        event.dataTransfer.effectAllowed = 'move';
        if (onDragStart) onDragStart(nodeType);
    };

    return (
        <div className="node-palette">
            <h3>Nodes</h3>
            {nodeTypes.map((nodeType) => {
                const Icon = nodeType.icon;
                return (
                    <div
                        key={nodeType.type}
                        className="node-item"
                        style={{ '--node-color': nodeType.color }}
                        draggable
                        onDragStart={(e) => handleDragStart(e, nodeType)}
                    >
                        <div className="node-item-icon" style={{ '--node-color': nodeType.color }}>
                            <Icon />
                        </div>
                        <div className="node-item-info">
                            <h4>{nodeType.name}</h4>
                            <p>{nodeType.description}</p>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

export default NodePalette;
