import { useState, useEffect } from 'react';
import { X, Settings, Zap, FileText, Wrench } from 'lucide-react';

const availableTools = [
    { id: 'http_request', name: 'HTTP Request' },
    { id: 'send_email', name: 'Send Email' },
    { id: 'database_query', name: 'Database Query' },
    { id: 'calendar_check', name: 'Calendar Check' },
    { id: 'knowledge_search', name: 'Knowledge Search' }
];

const PropertiesPanel = ({ node, onClose, onUpdate }) => {
    const [localData, setLocalData] = useState({});

    useEffect(() => {
        if (node) {
            setLocalData({
                label: node.data.label || '',
                customPrompt: node.data.config?.customPrompt || '',
                fieldName: node.data.config?.fieldName || '',
                condition: node.data.config?.condition || '',
                toolId: node.data.config?.toolId || '',
                includeMessages: node.data.context?.includeMessages || false,
                maxMessages: node.data.context?.maxMessages || 5,
                tools: node.data.tools || []
            });
        }
    }, [node]);

    if (!node) return null;

    const handleChange = (field, value) => {
        const newData = { ...localData, [field]: value };
        setLocalData(newData);

        // Update parent
        onUpdate(node.id, {
            ...node.data,
            label: newData.label,
            config: {
                ...node.data.config,
                customPrompt: newData.customPrompt,
                fieldName: newData.fieldName,
                condition: newData.condition,
                toolId: newData.toolId
            },
            context: {
                ...node.data.context,
                includeMessages: newData.includeMessages,
                maxMessages: parseInt(newData.maxMessages) || 5
            },
            tools: newData.tools
        });
    };

    const toggleTool = (toolId) => {
        const tools = localData.tools.includes(toolId)
            ? localData.tools.filter(t => t !== toolId)
            : [...localData.tools, toolId];
        handleChange('tools', tools);
    };

    return (
        <div className="properties-panel">
            <div className="properties-panel-header">
                <h3>Node Properties</h3>
                <button className="properties-panel-close" onClick={onClose}>
                    <X size={18} />
                </button>
            </div>

            <div className="properties-panel-body">
                {/* Basic Settings */}
                <div className="property-section">
                    <h4><Settings size={14} /> General</h4>

                    <div className="property-field">
                        <label>Node Name</label>
                        <input
                            type="text"
                            value={localData.label}
                            onChange={(e) => handleChange('label', e.target.value)}
                            placeholder="Enter node name..."
                        />
                    </div>
                </div>

                {/* LLM Node Settings */}
                {node.data.nodeType === 'llm' && (
                    <>
                        <div className="property-section">
                            <h4><FileText size={14} /> Prompt</h4>
                            <div className="property-field">
                                <label>System Prompt</label>
                                <textarea
                                    value={localData.customPrompt}
                                    onChange={(e) => handleChange('customPrompt', e.target.value)}
                                    placeholder="You are a helpful assistant..."
                                />
                            </div>
                        </div>

                        <div className="property-section">
                            <h4><Wrench size={14} /> Tools</h4>
                            <div className="property-field">
                                <label>Available Tools</label>
                                <div className="tool-chips">
                                    {availableTools.map((tool) => (
                                        <span
                                            key={tool.id}
                                            className={`tool-chip ${localData.tools.includes(tool.id) ? 'active' : ''}`}
                                            onClick={() => toggleTool(tool.id)}
                                        >
                                            {tool.name}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="property-section">
                            <h4><Zap size={14} /> Context</h4>
                            <div className="property-field">
                                <label className="toggle-switch">
                                    <input
                                        type="checkbox"
                                        checked={localData.includeMessages}
                                        onChange={(e) => handleChange('includeMessages', e.target.checked)}
                                    />
                                    <span className="toggle-track">
                                        <span className="toggle-thumb"></span>
                                    </span>
                                    <span className="toggle-label">Include message history</span>
                                </label>
                            </div>

                            {localData.includeMessages && (
                                <div className="property-field">
                                    <label>Max Messages</label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="50"
                                        value={localData.maxMessages}
                                        onChange={(e) => handleChange('maxMessages', e.target.value)}
                                    />
                                </div>
                            )}
                        </div>
                    </>
                )}

                {/* Gather Node Settings */}
                {node.data.nodeType === 'gather' && (
                    <div className="property-section">
                        <h4><FileText size={14} /> Configuration</h4>
                        <div className="property-field">
                            <label>Field Name</label>
                            <input
                                type="text"
                                value={localData.fieldName}
                                onChange={(e) => handleChange('fieldName', e.target.value)}
                                placeholder="customer_email"
                            />
                        </div>
                    </div>
                )}

                {/* Condition Node Settings */}
                {node.data.nodeType === 'condition' && (
                    <div className="property-section">
                        <h4><FileText size={14} /> Condition</h4>
                        <div className="property-field">
                            <label>Condition Expression</label>
                            <input
                                type="text"
                                value={localData.condition}
                                onChange={(e) => handleChange('condition', e.target.value)}
                                placeholder="intent == sales"
                            />
                        </div>
                    </div>
                )}

                {/* Tool Node Settings */}
                {node.data.nodeType === 'tool' && (
                    <div className="property-section">
                        <h4><Wrench size={14} /> Tool Configuration</h4>
                        <div className="property-field">
                            <label>Select Tool</label>
                            <select
                                value={localData.toolId}
                                onChange={(e) => handleChange('toolId', e.target.value)}
                            >
                                <option value="">Select a tool...</option>
                                {availableTools.map((tool) => (
                                    <option key={tool.id} value={tool.id}>
                                        {tool.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PropertiesPanel;
