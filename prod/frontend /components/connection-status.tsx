import { Circle } from "lucide-react"

interface ConnectionStatusProps {
  status: "connected" | "disconnected" | "connecting"
}

export function ConnectionStatus({ status }: ConnectionStatusProps) {
  const getStatusColor = () => {
    switch (status) {
      case "connected":
        return "text-green-500"
      case "disconnected":
        return "text-red-500"
      case "connecting":
        return "text-amber-500"
    }
  }

  return <Circle className={`h-3 w-3 fill-current ${getStatusColor()}`} />
}
