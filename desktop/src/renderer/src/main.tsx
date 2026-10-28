import React from 'react'
import ReactDOM from 'react-dom/client'
import './styles/globals.css'
import App from './App'

class Boundary extends React.Component<{ children: React.ReactNode }, { err: Error | null }> {
  state = { err: null as Error | null }
  static getDerivedStateFromError(err: Error) { return { err } }
  render() {
    if (this.state.err) {
      return (
        <pre style={{ padding: 16, color: '#b42318', whiteSpace: 'pre-wrap', font: '13px Consolas, monospace' }}>
          {'UI crashed:\n' + this.state.err.stack}
        </pre>
      )
    }
    return this.props.children
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <Boundary><App /></Boundary>
)