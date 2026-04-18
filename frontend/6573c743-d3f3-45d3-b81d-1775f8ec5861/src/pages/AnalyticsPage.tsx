import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer } from
'recharts';
import { Users, Eye, MousePointerClick, TrendingUp } from 'lucide-react';
const data = [
{
  name: 'Mon',
  engagement: 4000,
  reach: 2400
},
{
  name: 'Tue',
  engagement: 3000,
  reach: 1398
},
{
  name: 'Wed',
  engagement: 2000,
  reach: 9800
},
{
  name: 'Thu',
  engagement: 2780,
  reach: 3908
},
{
  name: 'Fri',
  engagement: 1890,
  reach: 4800
},
{
  name: 'Sat',
  engagement: 2390,
  reach: 3800
},
{
  name: 'Sun',
  engagement: 3490,
  reach: 4300
}];

export function AnalyticsPage() {
  const stats = [
  {
    label: 'Total Followers',
    value: '12.4K',
    change: '+12%',
    icon: Users,
    color: 'text-blue-500'
  },
  {
    label: 'Accounts Reached',
    value: '45.2K',
    change: '+24%',
    icon: Eye,
    color: 'text-green-500'
  },
  {
    label: 'Engagement Rate',
    value: '5.8%',
    change: '+1.2%',
    icon: MousePointerClick,
    color: 'text-brand'
  },
  {
    label: 'Profile Visits',
    value: '3.1K',
    change: '-2%',
    icon: TrendingUp,
    color: 'text-purple-500'
  }];

  return (
    <div className="max-w-6xl mx-auto pt-4 md:pt-8 px-4 pb-20">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold">Professional Dashboard</h1>
        <select className="bg-dark-800 border border-dark-600 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-brand">
          <option>Last 7 days</option>
          <option>Last 30 days</option>
          <option>Last 90 days</option>
        </select>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((stat, idx) =>
        <div
          key={idx}
          className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
          
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-xl bg-dark-900 ${stat.color}`}>
                <stat.icon size={24} />
              </div>
              <span
              className={`text-sm font-semibold ${stat.change.startsWith('+') ? 'text-green-500' : 'text-red-500'}`}>
              
                {stat.change}
              </span>
            </div>
            <p className="text-gray-400 text-sm mb-1">{stat.label}</p>
            <h3 className="text-2xl font-bold">{stat.value}</h3>
          </div>
        )}
      </div>

      {/* Chart Section */}
      <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6 mb-8">
        <h2 className="text-lg font-bold mb-6">Engagement Overview</h2>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{
                top: 5,
                right: 20,
                bottom: 5,
                left: 0
              }}>
              
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#262626"
                vertical={false} />
              
              <XAxis
                dataKey="name"
                stroke="#9CA3AF"
                tick={{
                  fill: '#9CA3AF'
                }}
                axisLine={false}
                tickLine={false} />
              
              <YAxis
                stroke="#9CA3AF"
                tick={{
                  fill: '#9CA3AF'
                }}
                axisLine={false}
                tickLine={false} />
              
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1A1A1A',
                  border: '1px solid #262626',
                  borderRadius: '8px'
                }}
                itemStyle={{
                  color: '#fff'
                }} />
              
              <Line
                type="monotone"
                dataKey="engagement"
                stroke="#E53E3E"
                strokeWidth={3}
                dot={{
                  fill: '#E53E3E',
                  strokeWidth: 2
                }}
                activeDot={{
                  r: 8
                }} />
              
              <Line
                type="monotone"
                dataKey="reach"
                stroke="#4B5563"
                strokeWidth={3}
                dot={{
                  fill: '#4B5563',
                  strokeWidth: 2
                }} />
              
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Content */}
      <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold">Top Performing Posts</h2>
          <button className="text-brand text-sm font-semibold hover:text-brand-hover">
            View All
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) =>
          <div
            key={i}
            className="group relative aspect-square rounded-xl overflow-hidden bg-dark-900 cursor-pointer">
            
              <img
              src={`https://picsum.photos/seed/top${i}/400/400`}
              alt="Post"
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
            
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-4">
                <span className="text-white font-bold text-sm">
                  12.4k Likes
                </span>
                <span className="text-gray-300 text-xs">842 Comments</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>);

}