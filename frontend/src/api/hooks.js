import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { clearToken, setToken } from "./auth";
import { api } from "./client";

export function useRegister() {
  return useMutation({
    mutationFn: async ({ username, email, password }) => {
      const response = await api.post("/auth/register/", { username, email, password });
      return response.data;
    },
    onSuccess: (data) => setToken(data.token),
  });
}

export function useLogin() {
  return useMutation({
    mutationFn: async ({ username, password }) => {
      const response = await api.post("/auth/login/", { username, password });
      return response.data;
    },
    onSuccess: (data) => setToken(data.token),
  });
}

export function useLogout() {
  return useMutation({
    mutationFn: async () => {
      try {
        await api.post("/auth/logout/");
      } finally {
        clearToken();
      }
    },
  });
}

export function useMe(enabled) {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => (await api.get("/auth/user/")).data,
    enabled,
    retry: false,
  });
}

export function useContracts() {
  return useQuery({
    queryKey: ["contracts"],
    queryFn: async () => (await api.get("/contracts/")).data,
  });
}

export function useContract(id) {
  return useQuery({
    queryKey: ["contracts", id],
    queryFn: async () => (await api.get(`/contracts/${id}/`)).data,
    enabled: id != null,
  });
}

export function usePlaybook() {
  return useQuery({
    queryKey: ["playbook"],
    queryFn: async () => (await api.get("/playbook/")).data,
  });
}

export function useChatMessages(contractId) {
  return useQuery({
    queryKey: ["chat", contractId],
    queryFn: async () => (await api.get(`/contracts/${contractId}/chat/`)).data,
    enabled: contractId != null,
  });
}

export function useSendChatMessage(contractId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (question) => (await api.post(`/contracts/${contractId}/chat/`, { question })).data,
    onSuccess: (data) => {
      queryClient.setQueryData(["chat", contractId], (existing) => [
        ...(existing || []),
        data.user_message,
        data.assistant_message,
      ]);
    },
  });
}

export function useDeleteContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (contractId) => {
      await api.delete(`/contracts/${contractId}/`);
      return contractId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
    },
  });
}

export function useDownloadReportPdf() {
  return useMutation({
    mutationFn: async (contractId) => {
      const response = await api.get(`/contracts/${contractId}/report.pdf`, { responseType: "blob" });
      const disposition = response.headers["content-disposition"] || "";
      const match = disposition.match(/filename="([^"]+)"/);
      const filename = match?.[1] || `ClauseGuard-report-${contractId}.pdf`;

      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    },
  });
}

export function useUploadContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, text, filename }) => {
      const form = new FormData();
      if (file) {
        form.append("file", file);
      } else {
        form.append("text", text);
        form.append("filename", filename || "pasted-contract.txt");
      }
      const response = await api.post("/contracts/", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
    },
  });
}
