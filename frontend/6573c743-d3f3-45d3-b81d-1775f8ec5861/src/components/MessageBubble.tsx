import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Reply, Edit2, Trash2, Check, CheckCheck, Clock,
  Heart, Smile, MoreVertical
} from 'lucide-react';
import { Message } from '../services/chatApi';

interface MessageBubbleProps {
  message: Message;
  isOwn: boolean;
  formatTime: (timestamp: string) => string;
  onReply: (message: Message) => void;
  onEdit: (message: Message) => void;
  onDelete: (messageId: string) => void;
  showActions: boolean;
  setShowActions: (messageId: string | null) => void;
  isEditing: boolean;
  editText: string;
  setEditText: (text: string) => void;
  onSaveEdit: () => void;
  onCancelEdit: () => void;
}

export function MessageBubble({
  message,
  isOwn,
  formatTime,
  onReply,
  onEdit,
  onDelete,
  showActions,
  setShowActions,
  isEditing,
  editText,
  setEditText,
  onSaveEdit,
  onCancelEdit
}: MessageBubbleProps) {
  const [showReactions, setShowReactions] = useState(false);

  const handleActionClick = (action: string) => {
    switch (action) {
      case 'reply':
        onReply(message);
        break;
      case 'edit':
        onEdit(message);
        break;
      case 'delete':
        onDelete(message.id);
        break;
    }
    setShowActions(null);
  };

  const renderContent = () => {
    if (isEditing) {
      return (
        <div className="flex items-end gap-2">
          <textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            className="flex-1 px-3 py-2 bg-white dark:bg-dark-800 border border-gray-200 dark:border-dark-600 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-brand"
            rows={1}
            autoFocus
          />
          <div className="flex gap-1">
            <button
              onClick={onCancelEdit}
              className="px-3 py-1 text-sm bg-gray-200 dark:bg-dark-700 rounded hover:bg-gray-300 dark:hover:bg-dark-600"
            >
              Cancel
            </button>
            <button
              onClick={onSaveEdit}
              disabled={!editText.trim()}
              className="px-3 py-1 text-sm bg-brand text-white rounded hover:bg-brand-hover disabled:opacity-50"
            >
              Save
            </button>
          </div>
        </div>
      );
    }

    return (
      <div>
        {/* Reply indicator */}
        {message.reply_to && (
          <div className="mb-2 p-2 bg-gray-100 dark:bg-dark-800 rounded-lg border-l-4 border-brand">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
              Replying to {message.reply_to.sender.first_name}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400 truncate">
              {message.reply_to.content}
            </div>
          </div>
        )}

        {/* Message content */}
        <div className={`whitespace-pre-wrap break-words ${
          message.is_edited ? 'italic' : ''
        }`}>
          {message.content}
        </div>

        {/* Reactions */}
        {message.reactions && message.reactions.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.reactions.map((reaction) => (
              <div
                key={reaction.id}
                className="flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-dark-800 rounded-full text-sm"
              >
                <span>{reaction.emoji}</span>
                <span className="text-xs text-gray-600 dark:text-gray-400">
                  {1} {/* Would need to count reactions by emoji */}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Message status */}
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {formatTime(message.created_at)}
          </span>
          
          {isOwn && (
            <div className="flex items-center gap-1">
              {message.is_read ? (
                <CheckCheck size={14} className="text-blue-500" />
              ) : (
                <Check size={14} className="text-gray-400" />
              )}
              {message.is_edited && (
                <span className="text-xs text-gray-400">(edited)</span>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isOwn ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div className={`max-w-xs lg:max-w-md xl:max-w-lg relative group ${
        isOwn ? 'order-2' : 'order-1'
      }`}>
        {/* Message bubble */}
        <div
          className={`relative px-4 py-2 rounded-2xl ${
            isOwn
              ? 'bg-brand text-white rounded-br-none'
              : 'bg-gray-100 dark:bg-dark-800 text-gray-900 dark:text-white rounded-bl-none'
          }`}
        >
          {/* Sender name for group messages */}
          {!isOwn && message.room_type === 'group' && (
            <div className="text-xs font-medium mb-1 opacity-75">
              {message.sender.first_name} {message.sender.last_name}
            </div>
          )}

          {renderContent()}

          {/* Action button */}
          {!isEditing && (
            <button
              onClick={() => setShowActions(showActions ? null : message.id)}
              className={`absolute -top-2 ${
                isOwn ? '-left-2' : '-right-2'
              } w-6 h-6 bg-white dark:bg-dark-900 rounded-full shadow-md border border-gray-200 dark:border-dark-700 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center`}
            >
              <MoreVertical size={12} className="text-gray-600 dark:text-gray-400" />
            </button>
          )}

          {/* Actions menu */}
          <AnimatePresence>
            {showActions && !isEditing && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className={`absolute top-0 ${
                  isOwn ? 'right-full mr-2' : 'left-full ml-2'
                } bg-white dark:bg-dark-900 rounded-lg shadow-lg border border-gray-200 dark:border-dark-700 py-1 z-10 min-w-max`}
              >
                {isOwn ? (
                  <>
                    <button
                      onClick={() => handleActionClick('edit')}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-800 flex items-center gap-2"
                    >
                      <Edit2 size={14} />
                      Edit
                    </button>
                    <button
                      onClick={() => handleActionClick('delete')}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-800 flex items-center gap-2 text-red-500"
                    >
                      <Trash2 size={14} />
                      Delete
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => handleActionClick('reply')}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-800 flex items-center gap-2"
                  >
                    <Reply size={14} />
                    Reply
                  </button>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Reactions menu */}
          <AnimatePresence>
            {showReactions && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className={`absolute top-full ${
                  isOwn ? 'right-0' : 'left-0'
                } mt-1 bg-white dark:bg-dark-900 rounded-lg shadow-lg border border-gray-200 dark:border-dark-700 p-2 z-10`}
              >
                <div className="flex gap-1">
                  {['\u2764\ufe0f', '\ud83d\ude0d', '\ud83d\ude02', '\ud83d\ude22', '\ud83d\ude0e', '\ud83d\udc4d', '\ud83d\udc4e'].map((emoji) => (
                  <button
                    key={emoji}
                    className="p-1 hover:bg-gray-100 dark:hover:bg-dark-800 rounded text-lg"
                  >
                    {emoji}
                  </button>
                ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Reaction button */}
        {!isEditing && (
          <button
            onClick={() => setShowReactions(!showReactions)}
            className={`absolute -bottom-2 ${
              isOwn ? 'right-2' : 'left-2'
            } w-6 h-6 bg-white dark:bg-dark-900 rounded-full shadow-md border border-gray-200 dark:border-dark-700 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center`}
          >
            <Smile size={12} className="text-gray-600 dark:text-gray-400" />
          </button>
        )}
      </div>
    </motion.div>
  );
}
