package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type LogLevel int

const (
	DEBUG LogLevel = iota
	INFO
	WARN
	ERROR
)

func (l LogLevel) String() string {
	switch l {
	case DEBUG:
		return "DEBUG"
	case INFO:
		return "INFO"
	case WARN:
		return "WARN"
	case ERROR:
		return "ERROR"
	default:
		return "UNKNOWN"
	}
}

type LogEntry struct {
	Timestamp float64 `json:"timestamp"`
	Level     string    `json:"level"`
	Message   string    `json:"message"`
	RequestID string    `json:"request_id,omitempty"`
	Logger    string    `json:"logger,omitempty"`
	Extra     map[string]interface{} `json:"extra,omitempty"`
}

type logMsg LogEntry

type TUIModel struct {
	logs   []LogEntry
	height int
	width  int
}

func NewTUIModel() *TUIModel {
	return &TUIModel{
		logs: make([]LogEntry, 0),
	}
}

func (m *TUIModel) Init() tea.Cmd {
	return tea.Batch(
		listenForLogs(),
	)
}

func (m *TUIModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.height = msg.Height
		m.width = msg.Width
	case logMsg:
		m.logs = append(m.logs, LogEntry(msg))
		// Keep only the last 1000 logs
		if len(m.logs) > 1000 {
			m.logs = m.logs[1:]
		}
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		}
	}
	return m, nil
}

func (m *TUIModel) View() string {
	if m.height == 0 {
		return "Loading..."
	}

	// Styles
	headerStyle := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#FAFAFA")).
		Background(lipgloss.Color("#7D56F4")).
		Padding(0, 1)

	debugStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("#626262"))
	infoStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("#04B575"))
	warnStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("#FFAA00"))
	errorStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("#FF4444"))

	// Header
	header := headerStyle.Render("SpeedBeaver Logger - Press 'q' or Ctrl+C to quit")
	
	// Calculate available space for logs
	availableHeight := m.height - 3 // Header + padding
	
	// Get recent logs that fit in the available space
	startIdx := 0
	if len(m.logs) > availableHeight {
		startIdx = len(m.logs) - availableHeight
	}
	
	var logLines []string
	for i := startIdx; i < len(m.logs); i++ {
		entry := m.logs[i]
		timestamp := time.Unix(int64(entry.Timestamp), int64((entry.Timestamp-float64(int64(entry.Timestamp)))*1e9)).Format("15:04:05.000")
		
		var levelStyle lipgloss.Style
		switch strings.ToUpper(entry.Level) {
		case "DEBUG":
			levelStyle = debugStyle
		case "INFO":
			levelStyle = infoStyle
		case "WARNING", "WARN":
			levelStyle = warnStyle
		case "ERROR":
			levelStyle = errorStyle
		default:
			levelStyle = infoStyle
		}
		
		// Format the log line
		levelStr := fmt.Sprintf("%-5s", strings.ToUpper(entry.Level))
		requestInfo := ""
		if entry.RequestID != "" {
			if len(entry.RequestID) > 8 {
				requestInfo = fmt.Sprintf(" [%s]", entry.RequestID[:8])
			} else {
				requestInfo = fmt.Sprintf(" [%s]", entry.RequestID)
			}
		}
		
		loggerInfo := ""
		if entry.Logger != "" {
			loggerInfo = fmt.Sprintf(" (%s)", entry.Logger)
		}
		
		logLine := fmt.Sprintf("%s %s%s%s %s",
			timestamp,
			levelStyle.Render(levelStr),
			requestInfo,
			loggerInfo,
			entry.Message,
		)
		
		// Truncate if too long
		if len(logLine) > m.width-2 {
			logLine = logLine[:m.width-5] + "..."
		}
		
		logLines = append(logLines, logLine)
	}
	
	// Build the complete view
	content := []string{header}
	content = append(content, "")
	content = append(content, logLines...)
	
	// Fill remaining space
	for len(content) < m.height {
		content = append(content, "")
	}
	
	return strings.Join(content, "\n")
}

func listenForLogs() tea.Cmd {
	return func() tea.Msg {
		scanner := bufio.NewScanner(os.Stdin)
		for scanner.Scan() {
			line := scanner.Text()
			if line == "" {
				continue
			}
			
			var entry LogEntry
			if err := json.Unmarshal([]byte(line), &entry); err != nil {
				now := time.Now()
				entry = LogEntry{
					Timestamp: float64(now.Unix()) + float64(now.Nanosecond())/1e9,
					Level:     "INFO",
					Message:   line,
				}
			}
			
			return logMsg(entry)
		}
		return tea.Quit()
	}
}

func main() {
	model := NewTUIModel()
	p := tea.NewProgram(model, tea.WithAltScreen())
	
	if _, err := p.Run(); err != nil {
		log.Fatalf("Error running TUI: %v", err)
	}
}